#!/usr/bin/env python3
"""
Python example for using the Enrollment API

Demonstrates programmatic agent enrollment using the requests library.
"""

import requests
import json
import sys
import os
from typing import Dict, Optional


class EnrollmentClient:
    """Client for CALDERA Enrollment API."""
    
    def __init__(self, caldera_url: str = "http://localhost:8888"):
        """
        Initialize enrollment client.
        
        Args:
            caldera_url: Base URL of Caldera instance
        """
        self.caldera_url = caldera_url
        self.api_base = f"{caldera_url}/plugin/enrollment"
    
    def health_check(self) -> Dict:
        """Check enrollment API health."""
        response = requests.get(f"{self.api_base}/health")
        response.raise_for_status()
        return response.json()
    
    def enroll_agent(
        self,
        platform: str,
        campaign_id: Optional[str] = None,
        tags: Optional[list] = None,
        hostname: Optional[str] = None
    ) -> Dict:
        """
        Create agent enrollment request.
        
        Args:
            platform: Target platform (linux, windows, darwin)
            campaign_id: Optional campaign UUID
            tags: Optional list of tags
            hostname: Optional hostname
        
        Returns:
            Enrollment response dictionary
        """
        payload = {
            "platform": platform,
        }
        
        if campaign_id:
            payload["campaign_id"] = campaign_id
        if tags:
            payload["tags"] = tags
        if hostname:
            payload["hostname"] = hostname
        
        response = requests.post(
            f"{self.api_base}/enroll",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def get_enrollment_status(self, request_id: str) -> Dict:
        """
        Get enrollment request status.
        
        Args:
            request_id: Enrollment request UUID
        
        Returns:
            Enrollment details dictionary
        """
        response = requests.get(f"{self.api_base}/enroll/{request_id}")
        response.raise_for_status()
        return response.json()
    
    def list_enrollments(
        self,
        campaign_id: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        List enrollment requests with filters.
        
        Args:
            campaign_id: Filter by campaign
            platform: Filter by platform
            status: Filter by status
            limit: Maximum results
        
        Returns:
            List of enrollment requests
        """
        params = {"limit": limit}
        if campaign_id:
            params["campaign_id"] = campaign_id
        if platform:
            params["platform"] = platform
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.api_base}/requests",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def list_campaign_agents(self, campaign_id: str) -> Dict:
        """
        List agents enrolled for a campaign.
        
        Args:
            campaign_id: Campaign UUID
        
        Returns:
            Campaign agents dictionary
        """
        response = requests.get(
            f"{self.api_base}/campaigns/{campaign_id}/agents"
        )
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of enrollment client."""
    
    # Get Caldera URL from environment or use default
    caldera_url = os.getenv("CALDERA_URL", "http://localhost:8888")
    
    print(f"Enrollment API Example")
    print(f"Caldera URL: {caldera_url}")
    print("=" * 50)
    print()
    
    # Initialize client
    client = EnrollmentClient(caldera_url)
    
    try:
        # Check API health
        print("1. Checking API health...")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Total requests: {health['total_requests']}")
        print()
        
        # Enroll a Linux agent
        print("2. Enrolling Linux agent...")
        linux_enrollment = client.enroll_agent(
            platform="linux",
            campaign_id="python-test-campaign",
            tags=["python-example", "localhost"],
            hostname="python-test-host"
        )
        print(f"   Request ID: {linux_enrollment['request_id']}")
        print(f"   Platform: {linux_enrollment['platform']}")
        print(f"   Campaign: {linux_enrollment['campaign_id']}")
        print()
        
        # Get enrollment status
        print("3. Checking enrollment status...")
        status = client.get_enrollment_status(linux_enrollment['request_id'])
        print(f"   Status: {status['status']}")
        print(f"   Created: {status['created_at']}")
        print()
        
        # Display bootstrap command
        print("4. Bootstrap command:")
        print(f"   {status['bootstrap_command']}")
        print()
        
        # List all enrollments
        print("5. Listing all enrollment requests...")
        all_enrollments = client.list_enrollments(limit=10)
        print(f"   Total: {all_enrollments['total']}")
        print(f"   Showing: {len(all_enrollments['requests'])} requests")
        print()
        
        # List enrollments for campaign
        print("6. Listing enrollments for python-test-campaign...")
        campaign_enrollments = client.list_enrollments(
            campaign_id="python-test-campaign"
        )
        print(f"   Total: {campaign_enrollments['total']}")
        print()
        
        # List campaign agents
        print("7. Listing agents for python-test-campaign...")
        campaign_agents = client.list_campaign_agents("python-test-campaign")
        print(f"   Total agents: {campaign_agents['total_agents']}")
        print()
        
        print("=" * 50)
        print("Example completed successfully!")
        print()
        print("To execute the bootstrap command on a Linux host:")
        print(f"  {status['bootstrap_command']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
