PIBUDDY_HOME=/opt/pibuddy
MINICONDA_HOME=/opt/miniconda3

# Create a new conda environment
# Make sure that conda is installed in a reacheable path.
# If it's /home/*, it's probablely not able to be ran by deamon service
conda create -p /opt/pibuddy/pyenv/pibuddy python=3.12

# Activate the environment
conda activate /opt/pibuddy/pyenv/pibuddy

# Install required packages
conda install flask python-dotenv -y

# Verify the installation
python -c "import flask; print(flask.__version__)"

# Copy the service file to systemd directory
sudo cp $PIBUDDY_HOME/pibuddy-web.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Start the service
sudo systemctl start pibuddy-web

# Enable the service to start on boot
sudo systemctl enable pibuddy-web

# Check the status of the service
sudo systemctl status pibuddy-web

# View service logs
sudo journalctl -u pibuddy-web -n 20 -f

# Check service status
sudo systemctl status pibuddy-web
