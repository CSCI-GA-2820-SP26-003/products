#!/bin/bash
#
# These must be installed as a user and therefore need to be run
# after the container has been created.
#
echo "**********************************************************************"
echo "Setting up Docker user development environment..."
echo "**********************************************************************"

echo "Setting up registry.local..."
sudo bash -c "echo '127.0.0.1    cluster-registry' >> /etc/hosts"

echo "Setting up insecure registry for cluster-registry..."
sudo mkdir -p /etc/docker
sudo bash -c 'cat > /etc/docker/daemon.json << EOF
{
    "insecure-registries": ["cluster-registry:5000"]
}
EOF'
sudo service docker restart || true

echo "Making git stop complaining about unsafe folders"
git config --global --add safe.directory /app

echo "**********************************************************************"
echo "Setup complete"
echo "**********************************************************************"
