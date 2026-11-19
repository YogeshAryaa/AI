# Local image and video generation

The Studio can send prompts to a local ComfyUI server. Ollama is used only to translate and improve prompts;
ComfyUI runs the image or video model. Ollama's standard API accepts images for vision tasks but does not
generate image or video files.

## Setup

1. Install and start [ComfyUI](https://github.com/comfyanonymous/ComfyUI) on the same machine or a trusted
   private network. Install the image/video model nodes and models required by your workflow.
2. In ComfyUI, build a workflow for each media type and export it using **Save (API Format)**.
3. Wrap each exported workflow in a JSON file with the graph and input-node mappings:

   ```json
   {
     "workflow": {
       "6": {
         "class_type": "CLIPTextEncode",
         "inputs": { "text": "prompt placeholder" }
       },
       "5": {
         "class_type": "EmptyLatentImage",
         "inputs": { "width": 512, "height": 512 }
       },
       "9": {
         "class_type": "SaveImage",
         "inputs": {}
       }
     },
     "inputs": {
       "prompt": "6.inputs.text",
       "width": "5.inputs.width",
       "height": "5.inputs.height"
     },
     "output_node": "9"
   }
   ```

   The workflow graph above is only a mapping example; use the complete graph exported by your ComfyUI setup.
   Image workflows must map `prompt`, `width`, and `height`; video workflows must also map `frames` to the model's
   frame-count input. `seed` is optional. Set `output_node` to the node that writes the final file. Video workflows
   must save an MP4, WebM, MOV, or MKV file.
4. Set these values in `backend/.env` and restart the backend:

   ```dotenv
   COMFYUI_URL=http://127.0.0.1:8188
   COMFYUI_IMAGE_WORKFLOW=C:\path\to\image-workflow.json
   COMFYUI_VIDEO_WORKFLOW=C:\path\to\video-workflow.json
   COMFYUI_TIMEOUT_SECONDS=900
   ```

   Use absolute paths. If ComfyUI runs in Docker, configure a URL reachable from the backend container (often
   `http://host.docker.internal:8188`) and make sure ComfyUI listens on an accessible interface.
5. In **AI providers**, add the Ollama provider and mark it **trusted/local**. The image and video tools use this
   local provider when prompt enhancement is enabled. You can turn enhancement off to send the prompt as entered.
   If the backend runs in Docker and Ollama runs on the host, set the Ollama provider URL to
   `http://host.docker.internal:11434/v1`.

## Use

- Open **Studio → AI image**, select **ComfyUI**, and create an image.
- Open **Studio → AI video**, choose frame shape and frame count, and create a clip.
- Generated videos appear in the Studio gallery and can be previewed or downloaded.
- Video files are saved in MongoDB and are limited to 12 MB per file. Use a smaller resolution or shorter clip if
  the workflow output exceeds that limit.

Each ComfyUI workflow is model-specific. Confirm that your exported API workflow includes a final output node and
that each mapping points to a real input in that workflow.
