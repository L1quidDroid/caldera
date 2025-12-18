#!/bin/bash
################################################################################
# Quick Commands Reference for Demo
################################################################################

CALDERA_IP="68.218.0.170"
RED_IP="4.197.184.112"
BLUE_IP="4.147.185.137"

echo "================================================"
echo "CALDERA Demo - Quick Commands"
echo "================================================"
echo ""

# Check setup status
check_status() {
    echo "📊 Current Status:"
    echo ""
    curl -s http://$CALDERA_IP:8888/api/v2/health 2>/dev/null && echo "✅ CALDERA: Running" || echo "❌ CALDERA: Not ready"
    curl -s http://$CALDERA_IP:5601 >/dev/null 2>&1 && echo "✅ Kibana: Running" || echo "❌ Kibana: Not ready"
    curl -s http://$CALDERA_IP:9200 >/dev/null 2>&1 && echo "✅ Elasticsearch: Running" || echo "❌ Elasticsearch: Not ready"
    echo ""
}

# List agents
list_agents() {
    echo "🤖 Registered Agents:"
    echo ""
    curl -s -u admin:admin http://$CALDERA_IP:8888/api/v2/agents | jq -r '.[] | "  - \(.paw): \(.platform) (\(.group)) - Last seen: \(.last_seen)"' 2>/dev/null || echo "  Unable to fetch agents"
    echo ""
}

# List operations
list_operations() {
    echo "⚙️  Operations:"
    echo ""
    curl -s -u admin:admin http://$CALDERA_IP:8888/api/v2/operations | jq -r '.[] | "  - \(.name): \(.state) - \(.host_group[0].paw // "no agents")"' 2>/dev/null || echo "  Unable to fetch operations"
    echo ""
}

# Deploy red agent via Azure
deploy_red_agent() {
    echo "🔴 Deploying Red Agent (Windows)..."
    az vm run-command invoke \
        --resource-group rg-caldera-demo-20251217-1842 \
        --name win-red-agent \
        --command-id RunPowerShellScript \
        --scripts @deploy_red_agent.ps1 \
        --no-wait
    echo "✅ Deployment started (running in background)"
    echo ""
}

# Deploy blue agent via Azure
deploy_blue_agent() {
    echo "🔵 Deploying Blue Agent (Linux)..."
    az vm run-command invoke \
        --resource-group rg-caldera-demo-20251217-1842 \
        --name linux-blue-agent \
        --command-id RunShellScript \
        --scripts @deploy_blue_agent.sh \
        --no-wait
    echo "✅ Deployment started (running in background)"
    echo ""
}

# Show URLs
show_urls() {
    echo "🌐 Service URLs:"
    echo ""
    echo "  CALDERA:       http://$CALDERA_IP:8888"
    echo "  Credentials:   admin / admin"
    echo ""
    echo "  Kibana:        http://$CALDERA_IP:5601"
    echo "  Elasticsearch: http://$CALDERA_IP:9200"
    echo ""
    echo "  Red Agent RDP: $RED_IP (tonyto / P@ssw0rd123!)"
    echo "  Blue Agent SSH: ssh tonyto@$BLUE_IP"
    echo ""
}

# VM management
vm_status() {
    echo "🖥️  VM Status:"
    echo ""
    az vm list -g rg-caldera-demo-20251217-1842 \
        --query '[].{Name:name, Status:powerState, Size:hardwareProfile.vmSize}' \
        -o table
    echo ""
}

stop_vms() {
    echo "🛑 Stopping all VMs..."
    az vm deallocate -g rg-caldera-demo-20251217-1842 -n caldera-elk-server --no-wait
    az vm deallocate -g rg-caldera-demo-20251217-1842 -n win-red-agent --no-wait
    az vm deallocate -g rg-caldera-demo-20251217-1842 -n linux-blue-agent --no-wait
    echo "✅ Shutdown initiated (running in background)"
    echo ""
}

start_vms() {
    echo "▶️  Starting all VMs..."
    az vm start -g rg-caldera-demo-20251217-1842 -n caldera-elk-server --no-wait
    az vm start -g rg-caldera-demo-20251217-1842 -n win-red-agent --no-wait
    az vm start -g rg-caldera-demo-20251217-1842 -n linux-blue-agent --no-wait
    echo "✅ Startup initiated (will take 2-3 minutes)"
    echo ""
}

# Cleanup
cleanup_all() {
    echo "🧹 Deleting all resources..."
    read -p "Are you sure? This cannot be undone. (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        az group delete --name rg-caldera-demo-20251217-1842 --yes --no-wait
        echo "✅ Deletion initiated (running in background)"
    else
        echo "❌ Cancelled"
    fi
    echo ""
}

# Show menu
show_menu() {
    echo "Quick Commands:"
    echo "  1. Check status           - ./quick_commands.sh status"
    echo "  2. List agents            - ./quick_commands.sh agents"
    echo "  3. List operations        - ./quick_commands.sh operations"
    echo "  4. Deploy red agent       - ./quick_commands.sh deploy-red"
    echo "  5. Deploy blue agent      - ./quick_commands.sh deploy-blue"
    echo "  6. Show URLs              - ./quick_commands.sh urls"
    echo "  7. VM status              - ./quick_commands.sh vms"
    echo "  8. Stop VMs (save $)      - ./quick_commands.sh stop"
    echo "  9. Start VMs              - ./quick_commands.sh start"
    echo " 10. Cleanup (delete all)   - ./quick_commands.sh cleanup"
    echo ""
}

# Parse command
case "$1" in
    status)
        check_status
        ;;
    agents)
        list_agents
        ;;
    operations)
        list_operations
        ;;
    deploy-red)
        deploy_red_agent
        ;;
    deploy-blue)
        deploy_blue_agent
        ;;
    urls)
        show_urls
        ;;
    vms)
        vm_status
        ;;
    stop)
        stop_vms
        ;;
    start)
        start_vms
        ;;
    cleanup)
        cleanup_all
        ;;
    *)
        show_menu
        ;;
esac
