sudo apt update
sudo apt install -y curl git jq
#############################################
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl status ollama
ollama --version
#############################################
# Optional GPU check
nvidia-smi
#############################################
# Choose a model that suits your needs, others not listed in the links are also available: 
# https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/blob/d9006465af6fc714af653e381fbfa55ead5af84b/Qwen3.5-9B-Q4_K_M.gguf
# https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF and https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF/blob/main/mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf
# https://huggingface.co/lmstudio-community/Qwen3.8-Flash-Next-GGUF
# Example used in this setup:
# Qwen3.5-9B-Q4_K_M.gguf
# After the file is downloaded via the browser:
ls -lh ~/Downloads/Qwen3.5-9B-Q4_K_M.gguf
#############################################
mkdir -p ~/models/qwen3.5-9b
#############################################
mv ~/Downloads/Qwen3.5-9B-Q4_K_M.gguf \
~/models/qwen3.5-9b/
#############################################
# Create the Ollama Modelfile
cat > ~/models/qwen3.5-9b/Modelfile <<'EOF'
FROM ./Qwen3.5-9B-Q4_K_M.gguf
PARAMETER num_ctx 32768
EOF
#############################################
# Import the model into Ollama
cd ~/models/qwen3.5-9b
ollama create qwen3.5-9b-local -f Modelfile
#############################################
# Verify the imported model
ollama list
ollama show qwen3.5-9b-local
#############################################
# Test the model
ollama run qwen3.5-9b-local
# Type /bye to exit the Ollama chat.
#############################################
# Download the OpenClaw installer. If the download fails, retry every 10 seconds.
until curl -fsSL https://openclaw.ai/install.sh \
-o /tmp/openclaw-install.sh
do
echo "Failed to download the installer — retrying in 10 seconds..."
sleep 10
done
#############################################
# Install OpenClaw without the onboarding wizard
bash /tmp/openclaw-install.sh --no-onboard
#############################################
# Reload the shell environment
source ~/.bashrc
hash -r
#############################################
# Launch OpenClaw with the local Qwen model
ollama launch openclaw --model qwen3.5-9b-local
