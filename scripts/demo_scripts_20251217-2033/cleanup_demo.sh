#!/bin/bash
# Cleanup demo environment
echo "🧹 Cleaning up demo environment..."
az group delete --name rg-caldera-demo-20251217-2023 --yes --no-wait
echo "✅ Cleanup initiated (runs in background)"
