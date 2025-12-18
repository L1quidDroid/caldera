#!/bin/bash
# Cleanup demo environment
echo "🧹 Cleaning up demo environment..."
az group delete --name rg-caldera-demo-20251217-1842 --yes --no-wait
echo "✅ Cleanup initiated (runs in background)"
