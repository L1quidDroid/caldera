#!/bin/bash
# Cleanup demo environment
echo "🧹 Cleaning up demo environment..."
az group delete --name rg-caldera-demo-20251221-1821 --yes --no-wait
echo "✅ Cleanup initiated (runs in background)"
