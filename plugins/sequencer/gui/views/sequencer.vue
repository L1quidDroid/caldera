<template>
  <div class="sequencer-container">
    <div class="header">
      <h1>🔄 Automated Operation Sequencer</h1>
      <p class="subtitle">Multi-step campaign execution with failure recovery</p>
    </div>

    <!-- Job List -->
    <div class="card">
      <h2>Active Jobs</h2>
      <div v-if="jobs.length === 0" class="empty-state">
        No sequence jobs running. Start a new sequence below.
      </div>
      <div v-else class="job-list">
        <div v-for="job in jobs" :key="job.job_id" class="job-item" :class="jobStatusClass(job.status)">
          <div class="job-header">
            <span class="job-name">{{ job.sequence_name }}</span>
            <span class="job-status" :class="'status-' + job.status">{{ job.status.toUpperCase() }}</span>
          </div>
          <div class="job-details">
            <span>Campaign: <code>{{ job.campaign_id }}</code></span>
            <span>Progress: {{ job.completed_steps }}/{{ job.total_steps }} steps</span>
            <span>Started: {{ formatTime(job.started_at) }}</span>
          </div>
          <div class="job-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: jobProgress(job) + '%' }"></div>
            </div>
          </div>
          <div class="job-actions">
            <button v-if="job.status === 'running'" @click="cancelJob(job.job_id)" class="btn btn-danger">
              Cancel
            </button>
            <button v-if="job.status === 'failed' || job.status === 'error'" @click="retryJob(job.job_id)" class="btn btn-warning">
              Retry
            </button>
            <button @click="viewJobDetails(job.job_id)" class="btn btn-primary">
              Details
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Start New Sequence -->
    <div class="card">
      <h2>Start New Sequence</h2>
      
      <div class="form-group">
        <label for="campaign-select">Campaign</label>
        <select id="campaign-select" v-model="newJob.campaign_id" class="form-control">
          <option value="">-- Select Campaign --</option>
          <option v-for="campaign in campaigns" :key="campaign.id" :value="campaign.id">
            {{ campaign.name }} ({{ campaign.id }})
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="sequence-select">Sequence Template</label>
        <select id="sequence-select" v-model="newJob.sequence_name" class="form-control" @change="onSequenceSelect">
          <option value="">-- Select Sequence --</option>
          <option v-for="seq in sequences" :key="seq.name" :value="seq.name">
            {{ seq.display_name }} ({{ seq.steps }} steps)
          </option>
        </select>
        <small v-if="selectedSequence" class="form-text">{{ selectedSequence.description }}</small>
      </div>

      <div class="form-row">
        <div class="form-group col-md-6">
          <label for="max-retries">Max Retries</label>
          <input id="max-retries" v-model.number="newJob.max_retries" type="number" min="1" max="10" class="form-control">
        </div>
        <div class="form-group col-md-6">
          <label for="timeout">Timeout (seconds)</label>
          <input id="timeout" v-model.number="newJob.timeout" type="number" min="60" max="3600" step="60" class="form-control">
        </div>
      </div>

      <button @click="startSequence" :disabled="!canStartSequence" class="btn btn-success btn-lg">
        🚀 Start Sequence
      </button>
    </div>

    <!-- Available Sequences -->
    <div class="card">
      <h2>Available Sequence Templates</h2>
      <div class="sequence-grid">
        <div v-for="seq in sequences" :key="seq.name" class="sequence-card">
          <h3>{{ seq.display_name }}</h3>
          <p>{{ seq.description }}</p>
          <div class="sequence-meta">
            <span class="badge">{{ seq.steps }} steps</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SequencerView',
  data() {
    return {
      jobs: [],
      campaigns: [],
      sequences: [],
      newJob: {
        campaign_id: '',
        sequence_name: '',
        max_retries: 3,
        timeout: 300
      },
      selectedSequence: null,
      pollInterval: null
    };
  },
  computed: {
    canStartSequence() {
      return this.newJob.campaign_id && this.newJob.sequence_name;
    }
  },
  mounted() {
    this.fetchJobs();
    this.fetchCampaigns();
    this.fetchSequences();
    
    // Poll for job updates every 5 seconds
    this.pollInterval = setInterval(() => {
      this.fetchJobs();
    }, 5000);
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  },
  methods: {
    async fetchJobs() {
      try {
        const response = await this.$api.get('/plugin/sequencer/api/jobs');
        this.jobs = response.data;
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
      }
    },
    
    async fetchCampaigns() {
      try {
        // Get campaigns from data store
        const response = await this.$api.get('/api/v2/operations');
        // Extract unique campaign IDs (simplified - adjust based on your data model)
        const campaignSet = new Set();
        response.data.forEach(op => {
          if (op.campaign_id) {
            campaignSet.add(op.campaign_id);
          }
        });
        
        this.campaigns = Array.from(campaignSet).map(id => ({
          id,
          name: `Campaign ${id.substring(0, 8)}`
        }));
      } catch (error) {
        console.error('Failed to fetch campaigns:', error);
      }
    },
    
    async fetchSequences() {
      try {
        const response = await this.$api.get('/plugin/sequencer/api/sequences');
        this.sequences = response.data;
      } catch (error) {
        console.error('Failed to fetch sequences:', error);
      }
    },
    
    async startSequence() {
      if (!this.canStartSequence) return;
      
      try {
        const payload = {
          campaign_id: this.newJob.campaign_id,
          sequence_name: this.newJob.sequence_name,
          max_retries: this.newJob.max_retries,
          timeout: this.newJob.timeout
        };
        
        const response = await this.$api.post('/plugin/sequencer/api/start', payload);
        
        // Reset form
        this.newJob = {
          campaign_id: '',
          sequence_name: '',
          max_retries: 3,
          timeout: 300
        };
        this.selectedSequence = null;
        
        // Refresh jobs
        await this.fetchJobs();
        
        this.$notify({
          type: 'success',
          message: `Sequence job started: ${response.data.job_id}`
        });
      } catch (error) {
        this.$notify({
          type: 'error',
          message: `Failed to start sequence: ${error.response?.data?.error || error.message}`
        });
      }
    },
    
    async cancelJob(jobId) {
      if (!confirm('Cancel this sequence job?')) return;
      
      try {
        await this.$api.post(`/plugin/sequencer/api/cancel/${jobId}`);
        await this.fetchJobs();
        
        this.$notify({
          type: 'info',
          message: 'Job cancelled'
        });
      } catch (error) {
        this.$notify({
          type: 'error',
          message: `Failed to cancel job: ${error.response?.data?.error || error.message}`
        });
      }
    },
    
    async retryJob(jobId) {
      try {
        const response = await this.$api.post(`/plugin/sequencer/api/retry/${jobId}`);
        await this.fetchJobs();
        
        this.$notify({
          type: 'success',
          message: `Job retried: ${response.data.job_id}`
        });
      } catch (error) {
        this.$notify({
          type: 'error',
          message: `Failed to retry job: ${error.response?.data?.error || error.message}`
        });
      }
    },
    
    async viewJobDetails(jobId) {
      try {
        const response = await this.$api.get(`/plugin/sequencer/api/status/${jobId}`);
        // TODO: Show modal with detailed job info
        console.log('Job details:', response.data);
        alert(JSON.stringify(response.data, null, 2));
      } catch (error) {
        this.$notify({
          type: 'error',
          message: `Failed to fetch job details: ${error.message}`
        });
      }
    },
    
    onSequenceSelect() {
      this.selectedSequence = this.sequences.find(s => s.name === this.newJob.sequence_name);
    },
    
    jobProgress(job) {
      if (job.total_steps === 0) return 0;
      return Math.round((job.completed_steps / job.total_steps) * 100);
    },
    
    jobStatusClass(status) {
      return `job-status-${status}`;
    },
    
    formatTime(isoString) {
      if (!isoString) return 'N/A';
      const date = new Date(isoString);
      return date.toLocaleString();
    }
  }
};
</script>

<style scoped>
.sequencer-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.job-item {
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  padding: 16px;
  transition: all 0.3s;
}

.job-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.job-status-running {
  border-color: #3b82f6;
}

.job-status-completed {
  border-color: #10b981;
}

.job-status-failed, .job-status-error {
  border-color: #ef4444;
}

.job-status-cancelled {
  border-color: #9ca3af;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.job-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-running {
  background: #dbeafe;
  color: #1e40af;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-failed, .status-error {
  background: #fee2e2;
  color: #991b1b;
}

.status-cancelled {
  background: #f3f4f6;
  color: #374151;
}

.job-details {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #666;
}

.job-details code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.85rem;
}

.job-progress {
  margin-bottom: 12px;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  transition: width 0.5s ease;
}

.job-actions {
  display: flex;
  gap: 8px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 1rem;
}

.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-text {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.875rem;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #d97706;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-lg {
  padding: 14px 28px;
  font-size: 1.1rem;
  width: 100%;
}

.sequence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.sequence-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  transition: all 0.2s;
}

.sequence-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.sequence-card h3 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1.1rem;
}

.sequence-card p {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 12px;
}

.sequence-meta {
  display: flex;
  gap: 8px;
}

.badge {
  background: #f3f4f6;
  color: #374151;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
