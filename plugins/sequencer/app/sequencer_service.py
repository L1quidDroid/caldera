"""
Sequencer Service

Backend service for managing automated operation sequences.
Wraps the CLI sequence_campaign logic with async job tracking and REST API.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from aiohttp import web
from aiohttp_jinja2 import template

from app.utility.base_service import BaseService


class SequencerService(BaseService):
    """Service for managing automated operation sequences."""
    
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.data_svc = services.get('data_svc')
        self.app_svc = services.get('app_svc')
        self.log = logging.getLogger('sequencer_service')
        
        # Job tracking
        self.jobs: Dict[str, Dict] = {}
        self.sequences_dir = Path('data/sequences')
        self.sequences_dir.mkdir(parents=True, exist_ok=True)
        
        # Load orchestrator CLI for sequencing
        import sys
        orchestrator_root = Path(__file__).parent.parent.parent / 'orchestrator'
        sys.path.insert(0, str(orchestrator_root))
        
        from orchestrator.cli import CalderaOrchestratorCLI
        self.orchestrator_cli = CalderaOrchestratorCLI()
    
    async def list_jobs(self, request: web.Request) -> web.Response:
        """GET /plugin/sequencer/api/jobs - List all sequence jobs."""
        jobs_list = [
            {
                'job_id': job_id,
                'campaign_id': job['campaign_id'],
                'sequence_name': job['sequence_name'],
                'status': job['status'],
                'started_at': job['started_at'],
                'completed_at': job.get('completed_at'),
                'current_step': job.get('current_step', 0),
                'total_steps': job.get('total_steps', 0),
                'completed_steps': len(job.get('completed_steps', [])),
                'failed_steps': len(job.get('failed_steps', []))
            }
            for job_id, job in self.jobs.items()
        ]
        
        # Sort by started_at descending
        jobs_list.sort(key=lambda x: x['started_at'], reverse=True)
        
        return web.json_response(jobs_list)
    
    async def start_sequence(self, request: web.Request) -> web.Response:
        """
        POST /plugin/sequencer/api/start
        
        Body:
        {
            "campaign_id": "campaign-123",
            "sequence_file": "path/to/sequence.yml" OR "sequence_name": "discovery",
            "max_retries": 3,
            "timeout": 300
        }
        """
        try:
            data = await request.json()
        except Exception as e:
            return web.json_response({'error': f'Invalid JSON: {e}'}, status=400)
        
        campaign_id = data.get('campaign_id')
        sequence_file = data.get('sequence_file')
        sequence_name = data.get('sequence_name')
        max_retries = data.get('max_retries', 3)
        timeout = data.get('timeout', 300)
        
        if not campaign_id:
            return web.json_response({'error': 'campaign_id required'}, status=400)
        
        # Resolve sequence file
        if sequence_name and not sequence_file:
            sequence_file = str(self.sequences_dir / f'{sequence_name}.yml')
        
        if not sequence_file or not Path(sequence_file).exists():
            return web.json_response({
                'error': f'Sequence file not found: {sequence_file}'
            }, status=400)
        
        # Create job
        job_id = str(uuid.uuid4())
        
        # Load sequence to get metadata
        try:
            with open(sequence_file, 'r') as f:
                sequence_spec = yaml.safe_load(f)
        except Exception as e:
            return web.json_response({'error': f'Failed to load sequence: {e}'}, status=400)
        
        job = {
            'job_id': job_id,
            'campaign_id': campaign_id,
            'sequence_file': sequence_file,
            'sequence_name': sequence_spec.get('name', 'Unnamed'),
            'status': 'running',
            'started_at': datetime.utcnow().isoformat(),
            'max_retries': max_retries,
            'timeout': timeout,
            'total_steps': len(sequence_spec.get('steps', [])),
            'current_step': 0,
            'completed_steps': [],
            'failed_steps': [],
            'task': None
        }
        
        self.jobs[job_id] = job
        
        # Start async task
        task = asyncio.create_task(self._run_sequence_job(job_id))
        job['task'] = task
        
        self.log.info(f'Started sequence job {job_id} for campaign {campaign_id}')
        
        return web.json_response({
            'job_id': job_id,
            'status': 'running',
            'message': 'Sequence job started'
        }, status=202)
    
    async def _run_sequence_job(self, job_id: str):
        """Background task to run sequence."""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        try:
            # Run sequence via orchestrator CLI
            success = await self.orchestrator_cli.sequence_campaign(
                campaign_id=job['campaign_id'],
                sequence_file=job['sequence_file'],
                max_retries=job['max_retries'],
                timeout=job['timeout']
            )
            
            # Update job status
            job['status'] = 'completed' if success else 'failed'
            job['completed_at'] = datetime.utcnow().isoformat()
            
            # Notify workflow service if available
            workflow_svc = self.services.get('workflow_svc')
            if workflow_svc:
                await workflow_svc.on_sequence_complete(job_id, job)
        
        except Exception as e:
            self.log.error(f'Sequence job {job_id} failed: {e}', exc_info=True)
            job['status'] = 'error'
            job['error'] = str(e)
            job['completed_at'] = datetime.utcnow().isoformat()
    
    async def get_status(self, request: web.Request) -> web.Response:
        """GET /plugin/sequencer/api/status/{job_id} - Get job status."""
        job_id = request.match_info['job_id']
        
        job = self.jobs.get(job_id)
        if not job:
            return web.json_response({'error': 'Job not found'}, status=404)
        
        # Don't include task in response
        response_job = {k: v for k, v in job.items() if k != 'task'}
        
        return web.json_response(response_job)
    
    async def retry_job(self, request: web.Request) -> web.Response:
        """POST /plugin/sequencer/api/retry/{job_id} - Retry failed job."""
        job_id = request.match_info['job_id']
        
        old_job = self.jobs.get(job_id)
        if not old_job:
            return web.json_response({'error': 'Job not found'}, status=404)
        
        if old_job['status'] not in ['failed', 'error']:
            return web.json_response({
                'error': f'Cannot retry job in status: {old_job["status"]}'
            }, status=400)
        
        # Create new job with same parameters
        new_job_id = str(uuid.uuid4())
        new_job = {
            'job_id': new_job_id,
            'campaign_id': old_job['campaign_id'],
            'sequence_file': old_job['sequence_file'],
            'sequence_name': old_job['sequence_name'],
            'status': 'running',
            'started_at': datetime.utcnow().isoformat(),
            'max_retries': old_job['max_retries'],
            'timeout': old_job['timeout'],
            'total_steps': old_job['total_steps'],
            'current_step': 0,
            'completed_steps': [],
            'failed_steps': [],
            'retry_of': job_id
        }
        
        self.jobs[new_job_id] = new_job
        
        # Start async task
        task = asyncio.create_task(self._run_sequence_job(new_job_id))
        new_job['task'] = task
        
        return web.json_response({
            'job_id': new_job_id,
            'status': 'running',
            'message': f'Retrying job {job_id}'
        }, status=202)
    
    async def cancel_job(self, request: web.Request) -> web.Response:
        """POST /plugin/sequencer/api/cancel/{job_id} - Cancel running job."""
        job_id = request.match_info['job_id']
        
        job = self.jobs.get(job_id)
        if not job:
            return web.json_response({'error': 'Job not found'}, status=404)
        
        if job['status'] != 'running':
            return web.json_response({
                'error': f'Cannot cancel job in status: {job["status"]}'
            }, status=400)
        
        # Cancel task
        task = job.get('task')
        if task and not task.done():
            task.cancel()
        
        job['status'] = 'cancelled'
        job['completed_at'] = datetime.utcnow().isoformat()
        
        return web.json_response({
            'job_id': job_id,
            'status': 'cancelled',
            'message': 'Job cancelled'
        })
    
    async def list_sequences(self, request: web.Request) -> web.Response:
        """GET /plugin/sequencer/api/sequences - List available sequence templates."""
        sequences = []
        
        for yml_file in self.sequences_dir.glob('*.yml'):
            try:
                with open(yml_file, 'r') as f:
                    spec = yaml.safe_load(f)
                
                sequences.append({
                    'name': yml_file.stem,
                    'display_name': spec.get('name', yml_file.stem),
                    'description': spec.get('description', ''),
                    'steps': len(spec.get('steps', [])),
                    'file': str(yml_file)
                })
            except Exception as e:
                self.log.warning(f'Failed to load sequence {yml_file}: {e}')
        
        return web.json_response(sequences)
    
    @template('sequencer.html')
    async def gui_view(self, request: web.Request):
        """Render sequencer GUI (legacy iframe mode)."""
        return {}
