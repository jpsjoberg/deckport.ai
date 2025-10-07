"""
ComfyUI Integration Service for Deckport Admin Panel
Handles communication with external ComfyUI server for AI art generation
"""

import os
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Optional, Any
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Service for interacting with ComfyUI API on external server"""
    
    def __init__(self, host: str = None, timeout: int = None, client_id: str = None):
        self.host = host or os.environ.get("COMFYUI_HOST", "https://c.getvideo.ai")
        self.timeout = timeout or int(os.environ.get("COMFYUI_TIMEOUT", "120"))
        self.client_id = client_id or os.environ.get("COMFYUI_CLIENT_ID", "deckport-admin")
        
        # Authentication credentials
        self.username = os.environ.get("COMFYUI_USERNAME")
        self.password = os.environ.get("COMFYUI_PASSWORD")
        
        # Ensure host doesn't end with slash
        if self.host.endswith('/'):
            self.host = self.host[:-1]
    
    def _get_auth(self) -> Optional[HTTPBasicAuth]:
        """Get HTTP Basic Auth if credentials are configured"""
        if self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        return None
    
    def is_online(self) -> bool:
        """Check if ComfyUI server is online and responsive"""
        try:
            response = requests.get(f"{self.host}/system_stats", timeout=10, auth=self._get_auth())
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"ComfyUI server check failed: {e}")
            return False
    
    def get_system_stats(self) -> Optional[Dict]:
        """Get ComfyUI system statistics"""
        try:
            response = requests.get(f"{self.host}/system_stats", timeout=10, auth=self._get_auth())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get system stats: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"System stats request failed: {e}")
            return None
    
    def load_workflow_template(self, workflow_path: str) -> Optional[Dict]:
        """Load ComfyUI workflow template from file"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workflow template: {e}")
            return None
    
    def inject_prompt(self, workflow: Dict, prompt: str, seed: Optional[int] = None) -> Dict:
        """Inject text prompt and optional seed into workflow"""
        updated_workflow = workflow.copy()
        
        # Find and update CLIPTextEncode node (usually node "6")
        for node_id, node in updated_workflow.items():
            if (isinstance(node, dict) and 
                node.get("class_type") == "CLIPTextEncode" and 
                "inputs" in node and 
                "text" in node["inputs"]):
                node["inputs"]["text"] = prompt
                break
        
        # Set seed if provided
        if seed is not None:
            for node_id, node in updated_workflow.items():
                if (isinstance(node, dict) and 
                    node.get("class_type") == "RandomNoise" and 
                    "inputs" in node):
                    node["inputs"]["noise_seed"] = int(seed)
                    break
        
        return updated_workflow
    
    def submit_prompt(self, workflow: Dict) -> Optional[str]:
        """Submit workflow to ComfyUI and return prompt ID"""
        try:
            url = f"{self.host}/prompt"
            payload = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout, auth=self._get_auth())
            
            if response.status_code >= 400:
                logger.error(f"ComfyUI prompt submission failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            prompt_id = data.get("prompt_id") or data.get("id")
            
            if not prompt_id:
                logger.error(f"No prompt ID returned from ComfyUI: {data}")
                return None
            
            logger.info(f"ComfyUI prompt submitted successfully: {prompt_id}")
            return prompt_id
            
        except Exception as e:
            logger.error(f"ComfyUI prompt submission error: {e}")
            return None
    
    def get_history(self, prompt_id: str = None) -> Optional[Dict]:
        """Get generation history, optionally for specific prompt ID"""
        try:
            if prompt_id:
                url = f"{self.host}/history/{prompt_id}"
            else:
                url = f"{self.host}/history"
            
            response = requests.get(url, timeout=30, auth=self._get_auth())
            
            if response.status_code >= 400:
                logger.error(f"History request failed: {response.status_code}")
                return None
            
            return response.json()
            
        except Exception as e:
            logger.error(f"History request error: {e}")
            return None
    
    def get_image_from_history(self, prompt_id: str) -> Optional[bytes]:
        """Extract first generated image from history"""
        try:
            history = self.get_history(prompt_id)
            if not history:
                return None
            
            # Handle different history response formats
            records = {}
            if isinstance(history, dict) and prompt_id in history:
                records = {prompt_id: history[prompt_id]}
            elif isinstance(history, dict):
                records = history
            
            # Search through outputs for images
            for record_id, record in records.items():
                outputs = record.get("outputs", {})
                for node_id, node_output in outputs.items():
                    images = node_output.get("images", [])
                    for image_info in images:
                        filename = image_info.get("filename")
                        if not filename:
                            continue
                        
                        # Download the image
                        subfolder = image_info.get("subfolder", "")
                        img_type = image_info.get("type", "output")
                        
                        view_url = (
                            f"{self.host}/view?"
                            f"filename={quote(filename)}&"
                            f"subfolder={quote(subfolder)}&"
                            f"type={quote(img_type)}"
                        )
                        
                        img_response = requests.get(view_url, timeout=30, auth=self._get_auth())
                        if img_response.status_code == 200:
                            logger.info(f"Successfully downloaded image: {filename}")
                            return img_response.content
            
            logger.warning(f"No images found in history for prompt {prompt_id}")
            return None
            
        except Exception as e:
            logger.error(f"Image extraction error: {e}")
            return None
    
    def wait_for_completion(self, prompt_id: str, max_wait: int = None) -> Optional[bytes]:
        """Wait for prompt completion and return generated image"""
        max_wait = max_wait or self.timeout
        start_time = time.time()
        check_interval = 2.0
        
        logger.info(f"Waiting for ComfyUI completion: {prompt_id}")
        
        while time.time() - start_time < max_wait:
            # Check if image is ready
            image_data = self.get_image_from_history(prompt_id)
            if image_data:
                elapsed = time.time() - start_time
                logger.info(f"ComfyUI generation completed in {elapsed:.1f}s")
                return image_data
            
            # Wait before next check
            time.sleep(check_interval)
            
            # Increase interval slightly to reduce server load
            check_interval = min(check_interval * 1.1, 10.0)
        
        logger.error(f"ComfyUI generation timeout after {max_wait}s for prompt {prompt_id}")
        return None
    
    def generate_card_art(self, prompt: str, seed: Optional[int] = None, 
                         workflow_path: str = None) -> Optional[bytes]:
        """
        Complete card art generation workflow
        
        Args:
            prompt: Text description for the artwork
            seed: Optional seed for reproducible generation
            workflow_path: Path to ComfyUI workflow JSON file
            
        Returns:
            Generated image as bytes, or None if failed
        """
        try:
            # Load workflow template
            if not workflow_path:
                workflow_path = "/home/jp/deckport.ai/cardmaker.ai/art-generation.json"
            
            workflow = self.load_workflow_template(workflow_path)
            if not workflow:
                logger.error("Failed to load workflow template")
                return None
            
            # Inject prompt and seed
            workflow = self.inject_prompt(workflow, prompt, seed)
            
            # Submit to ComfyUI
            prompt_id = self.submit_prompt(workflow)
            if not prompt_id:
                logger.error("Failed to submit prompt to ComfyUI")
                return None
            
            # Wait for completion and get image
            image_data = self.wait_for_completion(prompt_id)
            if not image_data:
                logger.error("Failed to get generated image")
                return None
            
            logger.info(f"Successfully generated card art ({len(image_data)} bytes)")
            return image_data
            
        except Exception as e:
            logger.error(f"Card art generation failed: {e}")
            return None
    
    def get_queue_status(self) -> Optional[Dict]:
        """Get current ComfyUI queue status"""
        try:
            response = requests.get(f"{self.host}/queue", timeout=10, auth=self._get_auth())
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Queue status request failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Queue status request error: {e}")
            return None
    
    def generate_arena_video(self, image_path: str, motion_type: str = "zoom_in", 
                           motion_strength: float = 0.3, duration_frames: int = 150,
                           workflow_path: str = None) -> Optional[str]:
        """
        Generate video clip from arena image using ComfyUI video workflow
        
        Args:
            image_path: Path to input arena image
            motion_type: Type of camera motion (zoom_in, pan_left, etc.)
            motion_strength: Strength of motion effect (0.1-1.0)
            duration_frames: Video length in frames (150 = 5s at 30fps)
            workflow_path: Path to ComfyUI video workflow JSON
            
        Returns:
            Path to generated video file, or None if failed
        """
        try:
            # Load video workflow template
            if not workflow_path:
                workflow_path = "/home/jp/deckport.ai/workflows/arena-video-generation.json"
            
            workflow = self.load_workflow_template(workflow_path)
            if not workflow:
                logger.error("Failed to load video workflow template")
                return None
            
            # Configure workflow for arena video generation
            # Set input image
            if "1" in workflow and "inputs" in workflow["1"]:
                workflow["1"]["inputs"]["image"] = image_path
            
            # Set motion parameters
            motion_prompt = f"""
            Cinematic {motion_type} camera movement for fantasy arena environment.
            Smooth, professional cinematography, atmospheric depth, subtle movement.
            High-quality video generation, motion strength: {motion_strength}.
            """
            
            if "2" in workflow and "inputs" in workflow["2"]:
                workflow["2"]["inputs"]["text"] = motion_prompt
            
            # Configure video settings
            if "4" in workflow and "inputs" in workflow["4"]:
                workflow["4"]["inputs"]["video_frames"] = duration_frames
                workflow["4"]["inputs"]["motion_bucket_id"] = int(motion_strength * 255)
            
            # Submit to ComfyUI
            prompt_id = self.submit_prompt(workflow)
            if not prompt_id:
                logger.error("Failed to submit video generation prompt to ComfyUI")
                return None
            
            # Wait for video completion (longer timeout for video)
            video_data = self.wait_for_completion(prompt_id, max_wait=300)
            if not video_data:
                logger.error("Failed to generate arena video")
                return None
            
            # Return path to generated video (ComfyUI saves it automatically)
            output_filename = workflow.get("7", {}).get("inputs", {}).get("filename_prefix", "arena_video")
            video_path = f"/tmp/ComfyUI_output/{output_filename}.mp4"
            
            if os.path.exists(video_path):
                logger.info(f"Successfully generated arena video: {video_path}")
                return video_path
            else:
                logger.error("Video file not found after generation")
                return None
            
        except Exception as e:
            logger.error(f"Arena video generation failed: {e}")
            return None
    
    def clear_queue(self) -> bool:
        """Clear the ComfyUI queue"""
        try:
            response = requests.post(f"{self.host}/queue", 
                                   json={"clear": True}, 
                                   timeout=10,
                                   auth=self._get_auth())
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Queue clear error: {e}")
            return False


# Global service instance
comfyui_service = ComfyUIService()


def get_comfyui_service() -> ComfyUIService:
    """Get the global ComfyUI service instance"""
    return comfyui_service
