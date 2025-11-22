# HuggingFace Integration

Deploy applications to HuggingFace Spaces directly from WYN360 CLI with automated setup and deployment.

## Features

- **Space Creation** - Create Streamlit/Gradio Spaces
- **File Upload** - Automatic code deployment
- **README Generation** - Professional documentation
- **Authentication** - Seamless HF token integration

## Setup

Set your HuggingFace token:
```bash
export HF_TOKEN=hf_your_huggingface_token
# or
export HUGGINGFACE_TOKEN=hf_your_huggingface_token
```

## Usage Examples

### Deploy Streamlit App
```
You: Deploy my Streamlit app to HuggingFace

WYN360:
✓ Created HuggingFace Space: username/my-streamlit-app
✓ Generated professional README.md
✓ Uploaded application files
✓ Space URL: https://huggingface.co/spaces/username/my-streamlit-app
```

### Create Gradio Interface
```
You: Create a Gradio space for my ML model

WYN360:
✓ Generated Gradio interface code
✓ Created HuggingFace Space
✓ Deployed model and dependencies
✓ Live demo available at: [Space URL]
```

For detailed examples, see [Usage Examples](../usage/use-cases.md#huggingface-examples).