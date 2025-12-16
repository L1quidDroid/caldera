#!/bin/bash
#
# Local Enrollment API Testing Script
# Tests enrollment endpoints on localhost Caldera instance
#

set -e

CALDERA_URL="${CALDERA_URL:-http://localhost:8888}"
ENROLLMENT_API="${CALDERA_URL}/plugin/enrollment"

echo "=================================="
echo "Enrollment API Local Testing"
echo "=================================="
echo "Caldera URL: $CALDERA_URL"
echo ""

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
echo "GET $ENROLLMENT_API/health"
echo ""
curl -s -X GET "$ENROLLMENT_API/health" | jq '.'
echo ""
echo ""

# Test 2: Enroll Linux Agent
echo -e "${YELLOW}Test 2: Enroll Linux Agent${NC}"
echo "POST $ENROLLMENT_API/enroll"
echo ""
LINUX_REQUEST=$(curl -s -X POST "$ENROLLMENT_API/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linux",
    "campaign_id": "test-campaign-001",
    "tags": ["test", "localhost"],
    "hostname": "test-linux-host"
  }')

echo "$LINUX_REQUEST" | jq '.'
LINUX_REQUEST_ID=$(echo "$LINUX_REQUEST" | jq -r '.request_id')
echo ""
echo -e "${GREEN}✓ Linux enrollment request created: $LINUX_REQUEST_ID${NC}"
echo ""

# Test 3: Enroll Windows Agent
echo -e "${YELLOW}Test 3: Enroll Windows Agent${NC}"
echo "POST $ENROLLMENT_API/enroll"
echo ""
WINDOWS_REQUEST=$(curl -s -X POST "$ENROLLMENT_API/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "windows",
    "campaign_id": "test-campaign-001",
    "tags": ["test", "localhost"],
    "hostname": "test-windows-host"
  }')

echo "$WINDOWS_REQUEST" | jq '.'
WINDOWS_REQUEST_ID=$(echo "$WINDOWS_REQUEST" | jq -r '.request_id')
echo ""
echo -e "${GREEN}✓ Windows enrollment request created: $WINDOWS_REQUEST_ID${NC}"
echo ""

# Test 4: Get Enrollment Status
echo -e "${YELLOW}Test 4: Get Enrollment Status${NC}"
echo "GET $ENROLLMENT_API/enroll/$LINUX_REQUEST_ID"
echo ""
curl -s -X GET "$ENROLLMENT_API/enroll/$LINUX_REQUEST_ID" | jq '.'
echo ""
echo ""

# Test 5: List All Enrollment Requests
echo -e "${YELLOW}Test 5: List All Enrollment Requests${NC}"
echo "GET $ENROLLMENT_API/requests"
echo ""
curl -s -X GET "$ENROLLMENT_API/requests" | jq '.'
echo ""
echo ""

# Test 6: List Enrollment Requests by Campaign
echo -e "${YELLOW}Test 6: Filter by Campaign${NC}"
echo "GET $ENROLLMENT_API/requests?campaign_id=test-campaign-001"
echo ""
curl -s -X GET "$ENROLLMENT_API/requests?campaign_id=test-campaign-001" | jq '.'
echo ""
echo ""

# Test 7: List Campaign Agents
echo -e "${YELLOW}Test 7: List Campaign Agents${NC}"
echo "GET $ENROLLMENT_API/campaigns/test-campaign-001/agents"
echo ""
curl -s -X GET "$ENROLLMENT_API/campaigns/test-campaign-001/agents" | jq '.'
echo ""
echo ""

# Test 8: Error Handling - Invalid Platform
echo -e "${YELLOW}Test 8: Error Handling - Invalid Platform${NC}"
echo "POST $ENROLLMENT_API/enroll (with invalid platform)"
echo ""
curl -s -X POST "$ENROLLMENT_API/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "invalid-platform"
  }' | jq '.'
echo ""
echo ""

# Test 9: Error Handling - Missing Platform
echo -e "${YELLOW}Test 9: Error Handling - Missing Platform${NC}"
echo "POST $ENROLLMENT_API/enroll (without platform)"
echo ""
curl -s -X POST "$ENROLLMENT_API/enroll" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'
echo ""
echo ""

echo -e "${GREEN}=================================="
echo "All tests completed!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review enrollment requests in Caldera data directory"
echo "2. Execute bootstrap commands on target hosts"
echo "3. Verify agents appear in Caldera UI"
echo ""
echo "Bootstrap command for Linux:"
echo "$LINUX_REQUEST" | jq -r '.bootstrap_command'
echo ""
