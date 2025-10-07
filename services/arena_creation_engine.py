#!/usr/bin/env python3
"""
AI Arena Creation Engine
Generates complete arenas with LLM data, AI images, video clips, and music
Implements 8-step pipeline for creating immersive game environments
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

import requests
import anthropic
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from elevenlabs import ElevenLabs

# Import existing ComfyUI service
import sys
sys.path.append('/home/jp/deckport.ai')
from frontend.services.comfyui_service import ComfyUIService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArenaCreationEngine:
    """
    Complete AI-powered arena creation system
    Creates arenas with LLM data, AI images, video clips, and synchronized music
    """
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.elevenlabs_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        self.comfyui_service = ComfyUIService()
        
        # Paths
        self.base_path = Path('/home/jp/deckport.ai')
        self.assets_path = self.base_path / 'static' / 'arenas'
        self.temp_path = self.base_path / 'temp' / 'arena_creation'
        
        # Create directories
        self.assets_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Arena types and themes
        self.mana_colors = ['CRIMSON', 'AZURE', 'VERDANT', 'OBSIDIAN', 'RADIANT', 'AETHER']
        self.arena_themes = [
            'ancient_temple', 'crystal_cavern', 'floating_island', 'underwater_ruins',
            'volcanic_crater', 'frozen_tundra', 'mystical_forest', 'desert_oasis',
            'celestial_observatory', 'shadow_realm', 'steampunk_factory', 'ethereal_void'
        ]
    
    async def create_arenas_batch(self, count: int = 10) -> List[Dict]:
        """
        Create multiple arenas using the 8-step AI pipeline
        
        Args:
            count: Number of arenas to create (1-100)
            
        Returns:
            List of created arena data
        """
        if count < 1 or count > 100:
            raise ValueError("Arena count must be between 1 and 100")
        
        logger.info(f"🏗️ Starting creation of {count} arenas...")
        created_arenas = []
        
        for i in range(count):
            try:
                logger.info(f"🏟️ Creating arena {i+1}/{count}")
                arena_data = await self.create_single_arena(i)
                created_arenas.append(arena_data)
                logger.info(f"✅ Arena '{arena_data['name']}' created successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to create arena {i+1}: {e}")
                continue
        
        logger.info(f"🎉 Created {len(created_arenas)} arenas successfully!")
        return created_arenas
    
    async def create_single_arena(self, index: int) -> Dict:
        """
        Create a single arena using the 8-step pipeline
        
        Steps:
        1. Create arena data with LLM
        2. Insert data into database
        3. Generate 10+ arena environment images
        4. Create video clips from images
        5. Edit clips into sequences
        6. Generate music with ElevenLabs
        7. Sync music with video
        8. Create all arena video types (intro, ambient, etc.)
        """
        
        # Step 1: Create arena data with LLM
        logger.info("Step 1: Generating arena data with LLM...")
        arena_data = await self.generate_arena_data_llm(index)
        
        # Step 2: Insert into database
        logger.info("Step 2: Inserting arena data into database...")
        arena_id = await self.insert_arena_database(arena_data)
        arena_data['id'] = arena_id
        
        # Step 3: Generate arena environment images
        logger.info("Step 3: Generating arena environment images...")
        image_paths = await self.generate_arena_images(arena_data)
        
        # Step 4: Create video clips from images
        logger.info("Step 4: Creating video clips from images...")
        video_clips = await self.create_video_clips(image_paths, arena_data)
        
        # Step 5: Edit clips into sequences
        logger.info("Step 5: Editing clips into sequences...")
        video_sequences = await self.edit_clip_sequences(video_clips, arena_data)
        
        # Step 6: Generate music with ElevenLabs
        logger.info("Step 6: Generating arena music...")
        music_tracks = await self.generate_arena_music(arena_data)
        
        # Step 7: Sync music with video
        logger.info("Step 7: Synchronizing music with video...")
        final_videos = await self.sync_music_video(video_sequences, music_tracks, arena_data)
        
        # Step 8: Create all arena video types
        logger.info("Step 8: Creating specialized arena videos...")
        arena_videos = await self.create_arena_video_types(final_videos, arena_data)
        
        # Update database with video paths
        await self.update_arena_videos(arena_id, arena_videos)
        
        return arena_data
    
    async def generate_arena_data_llm(self, index: int) -> Dict:
        """
        Step 1: Generate comprehensive arena data using Claude
        """
        mana_color = self.mana_colors[index % len(self.mana_colors)]
        theme = self.arena_themes[index % len(self.arena_themes)]
        
        prompt = f"""Create a unique fantasy battle arena for a trading card game.

REQUIREMENTS:
- Mana Color: {mana_color}
- Theme: {theme}
- Must be unique and interesting
- Include gameplay mechanics that match the mana color

Generate a JSON object with exactly these fields:
1. name: Arena name (2-4 words)
2. mana_color: "{mana_color}"
3. passive_effect: {{name, description, type}}
4. objective: {{name, description, reward}}
5. hazard: {{name, description, trigger, effect}}
6. story_text: Rich lore (2-3 sentences)
7. flavor_text: Atmospheric quote (1 sentence)
8. special_rules: Gameplay modifications
9. difficulty_rating: 1-5 scale
10. environment_description: Detailed visual description for image generation (focus on architecture, lighting, atmosphere - no creatures or characters)

Make it thematically consistent with {mana_color} mana and {theme} theme.
Return ONLY the JSON object, no other text."""

        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.8,
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        
        arena_data = json.loads(response.content[0].text)
        
        # Add technical fields
        arena_data.update({
            'background_music': f"{arena_data['name'].lower().replace(' ', '_')}_ambient.ogg",
            'ambient_sounds': f"{arena_data['name'].lower().replace(' ', '_')}_sounds.ogg",
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        return arena_data
    
    async def insert_arena_database(self, arena_data: Dict) -> int:
        """
        Step 2: Insert arena data into database
        """
        from shared.database.connection import SessionLocal
        from shared.models.arena import Arena
        
        with SessionLocal() as session:
            arena = Arena(
                name=arena_data['name'],
                mana_color=arena_data['mana_color'],
                passive_effect=arena_data['passive_effect'],
                objective=arena_data['objective'],
                hazard=arena_data['hazard'],
                story_text=arena_data['story_text'],
                flavor_text=arena_data['flavor_text'],
                background_music=arena_data['background_music'],
                ambient_sounds=arena_data['ambient_sounds'],
                special_rules=arena_data['special_rules'],
                difficulty_rating=arena_data['difficulty_rating']
            )
            
            session.add(arena)
            session.commit()
            session.refresh(arena)
            
            return arena.id
    
    async def generate_arena_images(self, arena_data: Dict) -> List[str]:
        """
        Step 3: Generate 10+ arena environment images using ComfyUI workflow
        """
        arena_name = arena_data['name'].lower().replace(' ', '_')
        images_dir = self.assets_path / 'images' / arena_name
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Check ComfyUI availability
        if not self.comfyui_service.is_online():
            logger.error("ComfyUI service is not online")
            return []
        
        # Load the arena-specific ComfyUI workflow template
        arena_workflow_path = self.base_path / 'workflows' / 'arena-generation.json'
        if not arena_workflow_path.exists():
            # Fallback to card generation workflow and modify it
            arena_workflow_path = self.base_path / 'cardmaker.ai' / 'art-generation.json'
        
        # Base prompt for arena environment
        base_prompt = f"""
        {arena_data['environment_description']}
        
        High-quality fantasy battle arena environment, {arena_data['mana_color'].lower()} themed.
        Cinematic lighting, detailed architecture, atmospheric effects.
        Professional game environment art style, widescreen composition.
        Ultra-detailed digital painting, no creatures, no characters, no text.
        """
        
        # Negative prompt to exclude unwanted elements  
        negative_prompt = """
        humans, creatures, monsters, characters, people, text, UI, interface, 
        weapons, blood, corpses, signs, writing, logos, characters, figures,
        animals, beasts, dragons, knights, wizards, warriors
        """
        
        # Different camera angles and lighting conditions
        angle_variations = [
            "wide establishing shot from above, aerial perspective",
            "ground level perspective looking up at towering structures", 
            "dramatic low angle view emphasizing scale",
            "aerial bird's eye view showing full arena layout",
            "close-up architectural details and textures",
            "panoramic wide shot showing arena boundaries",
            "dramatic side angle highlighting key features",
            "looking through archways or entrance structures",
            "from inside arena looking outward",
            "golden hour sunset lighting, warm atmosphere",
            "dawn lighting with soft morning mist",
            "dramatic storm lighting with dark clouds"
        ]
        
        image_paths = []
        
        for i, angle in enumerate(angle_variations):
            try:
                # Create full prompt with angle variation
                full_prompt = f"{base_prompt}\n\nCamera angle and composition: {angle}"
                
                # Load and modify workflow for this generation
                workflow = self.comfyui_service.load_workflow_template(str(arena_workflow_path))
                if not workflow:
                    logger.error(f"Failed to load ComfyUI workflow template")
                    continue
                
                # Inject prompt into workflow (node 6 is typically the positive prompt)
                workflow = self.comfyui_service.inject_prompt(workflow, full_prompt)
                
                # Add negative prompt if workflow supports it (check for negative prompt node)
                if "7" in workflow and "inputs" in workflow["7"]:  # Node 7 is often negative prompt
                    workflow["7"]["inputs"]["text"] = negative_prompt
                
                # Set arena-appropriate dimensions (widescreen for environments)
                if "29" in workflow and "inputs" in workflow["29"]:  # Dimensions node
                    workflow["29"]["inputs"]["width"] = 1792
                    workflow["29"]["inputs"]["height"] = 1024
                
                # Set output path
                image_path = images_dir / f"{arena_name}_angle_{i+1:02d}.png"
                if "40" in workflow and "inputs" in workflow["40"]:  # Save node
                    workflow["40"]["inputs"]["path"] = str(image_path)
                
                # Submit to ComfyUI
                prompt_id = self.comfyui_service.submit_prompt(workflow)
                if not prompt_id:
                    logger.error(f"Failed to submit ComfyUI prompt for image {i+1}")
                    continue
                
                # Wait for completion
                image_data = self.comfyui_service.wait_for_completion(prompt_id)
                if image_data and image_path.exists():
                    image_paths.append(str(image_path))
                    logger.info(f"   Generated image {i+1}/{len(angle_variations)}: {angle}")
                else:
                    logger.error(f"ComfyUI generation failed for image {i+1}")
                
                # Rate limiting for ComfyUI
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to generate image {i+1}: {e}")
                continue
        
        return image_paths
    
    async def create_video_clips(self, image_paths: List[str], arena_data: Dict) -> List[str]:
        """
        Step 4: Create video clips from images using ComfyUI video generation workflow
        """
        arena_name = arena_data['name'].lower().replace(' ', '_')
        clips_dir = self.assets_path / 'clips' / arena_name
        clips_dir.mkdir(parents=True, exist_ok=True)
        
        # Check ComfyUI availability
        if not self.comfyui_service.is_online():
            logger.error("ComfyUI service is not online for video generation")
            return []
        
        # Load the arena video generation workflow
        video_workflow_path = self.base_path / 'workflows' / 'arena-video-generation.json'
        if not video_workflow_path.exists():
            logger.error("Arena video generation workflow not found")
            return []
        
        video_clips = []
        
        # Motion types for variety
        motion_types = [
            {"type": "zoom_in", "strength": 0.3, "description": "slow zoom in"},
            {"type": "zoom_out", "strength": 0.2, "description": "subtle zoom out"},
            {"type": "pan_left", "strength": 0.4, "description": "gentle pan left"},
            {"type": "pan_right", "strength": 0.4, "description": "gentle pan right"},
            {"type": "parallax", "strength": 0.25, "description": "parallax depth effect"},
            {"type": "orbit", "strength": 0.3, "description": "subtle orbital movement"},
            {"type": "dolly_in", "strength": 0.35, "description": "dolly camera movement"},
            {"type": "tilt_up", "strength": 0.2, "description": "slow tilt upward"},
            {"type": "atmospheric", "strength": 0.15, "description": "atmospheric breathing"},
            {"type": "cinematic", "strength": 0.4, "description": "cinematic sweep"}
        ]
        
        for i, image_path in enumerate(image_paths):
            try:
                # Select motion type for this clip
                motion = motion_types[i % len(motion_types)]
                
                clip_path = clips_dir / f"{arena_name}_clip_{i+1:02d}.mp4"
                
                # Generate video using ComfyUI service
                generated_video_path = self.comfyui_service.generate_arena_video(
                    image_path=str(image_path),
                    motion_type=motion['type'],
                    motion_strength=motion['strength'],
                    duration_frames=150,  # 5 seconds at 30fps
                    workflow_path=str(video_workflow_path)
                )
                
                if generated_video_path and os.path.exists(generated_video_path):
                    # Move video to our clips directory
                    shutil.move(generated_video_path, str(clip_path))
                    video_clips.append(str(clip_path))
                    logger.info(f"   Created video clip {i+1}/{len(image_paths)}: {motion['description']}")
                else:
                    logger.error(f"ComfyUI video generation failed for clip {i+1}")
                
                # Rate limiting for video generation (more intensive)
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Failed to create video clip {i+1}: {e}")
                continue
        
        return video_clips
    
    async def edit_clip_sequences(self, video_clips: List[str], arena_data: Dict) -> Dict[str, str]:
        """
        Step 5: Edit clips into different sequences for various arena video types
        """
        arena_name = arena_data['name'].lower().replace(' ', '_')
        sequences_dir = self.assets_path / 'sequences' / arena_name
        sequences_dir.mkdir(parents=True, exist_ok=True)
        
        sequences = {}
        
        # Create different sequences for different purposes
        sequence_configs = {
            'main': {
                'clips': video_clips[:6],  # First 6 clips
                'duration': 30,
                'description': 'Main arena showcase'
            },
            'intro': {
                'clips': video_clips[:3],  # First 3 clips
                'duration': 15,
                'description': 'Arena introduction'
            },
            'ambient': {
                'clips': video_clips[3:8],  # Middle clips
                'duration': 60,
                'description': 'Ambient background loop'
            },
            'victory': {
                'clips': video_clips[-3:],  # Last 3 clips
                'duration': 10,
                'description': 'Victory celebration'
            },
            'hazard': {
                'clips': video_clips[1:4],  # Dramatic clips
                'duration': 8,
                'description': 'Hazard activation'
            }
        }
        
        for seq_name, config in sequence_configs.items():
            try:
                output_path = sequences_dir / f"{arena_name}_{seq_name}.mp4"
                
                # Load video clips
                clips = []
                for clip_path in config['clips']:
                    if os.path.exists(clip_path):
                        clip = VideoFileClip(clip_path)
                        clips.append(clip)
                
                if clips:
                    # Create sequence with crossfades
                    if len(clips) > 1:
                        # Add crossfade transitions
                        final_clip = clips[0]
                        for clip in clips[1:]:
                            final_clip = final_clip.crossfadein(0.5).crossfadeout(0.5)
                            final_clip = final_clip.concatenate_videoclip(clip.crossfadein(0.5))
                    else:
                        final_clip = clips[0]
                    
                    # Adjust duration
                    target_duration = config['duration']
                    if final_clip.duration > target_duration:
                        final_clip = final_clip.subclip(0, target_duration)
                    elif final_clip.duration < target_duration:
                        # Loop the clip to reach target duration
                        loops_needed = int(target_duration / final_clip.duration) + 1
                        final_clip = final_clip.loop(n=loops_needed).subclip(0, target_duration)
                    
                    # Export
                    final_clip.write_videofile(
                        str(output_path),
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        verbose=False,
                        logger=None
                    )
                    
                    sequences[seq_name] = str(output_path)
                    logger.info(f"   Created {seq_name} sequence ({config['duration']}s)")
                    
                    # Clean up
                    final_clip.close()
                    for clip in clips:
                        clip.close()
                
            except Exception as e:
                logger.error(f"Failed to create {seq_name} sequence: {e}")
                continue
        
        return sequences
    
    async def generate_arena_music(self, arena_data: Dict) -> Dict[str, str]:
        """
        Step 6: Generate music for arena using ElevenLabs Music API
        """
        arena_name = arena_data['name'].lower().replace(' ', '_')
        music_dir = self.assets_path / 'music' / arena_name
        music_dir.mkdir(parents=True, exist_ok=True)
        
        # Music prompts for different arena video types
        music_configs = {
            'main': {
                'prompt': f"Epic fantasy orchestral music for {arena_data['name']} arena, {arena_data['mana_color'].lower()} themed, cinematic and atmospheric, 30 seconds",
                'duration': 30
            },
            'intro': {
                'prompt': f"Dramatic introduction music for {arena_data['name']}, building tension and excitement, {arena_data['mana_color'].lower()} magical theme, 15 seconds",
                'duration': 15
            },
            'ambient': {
                'prompt': f"Ambient background music for {arena_data['name']}, subtle and atmospheric, {arena_data['mana_color'].lower()} themed, loopable, 60 seconds",
                'duration': 60
            },
            'victory': {
                'prompt': f"Triumphant victory music for {arena_data['name']}, celebratory and epic, {arena_data['mana_color'].lower()} themed, 10 seconds",
                'duration': 10
            },
            'hazard': {
                'prompt': f"Dangerous hazard music for {arena_data['name']}, tense and ominous, {arena_data['mana_color'].lower()} themed, 8 seconds",
                'duration': 8
            }
        }
        
        music_tracks = {}
        
        for music_type, config in music_configs.items():
            try:
                output_path = music_dir / f"{arena_name}_{music_type}.mp3"
                
                # Generate music using ElevenLabs Music API
                # Note: Using the ElevenLabs Music capabilities from https://elevenlabs.io/docs/capabilities/music
                audio = self.elevenlabs_client.generate(
                    text=config['prompt'],
                    model="eleven_music_v1",  # ElevenLabs music model
                    voice_settings={
                        "stability": 0.7,
                        "similarity_boost": 0.8,
                        "style": 0.6,
                        "use_speaker_boost": True
                    }
                )
                
                # Save the generated audio
                with open(output_path, 'wb') as f:
                    for chunk in audio:
                        f.write(chunk)
                
                music_tracks[music_type] = str(output_path)
                logger.info(f"   Generated {music_type} music ({config['duration']}s)")
                
                # Rate limiting for API
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to generate {music_type} music: {e}")
                # Create silent audio as fallback
                music_tracks[music_type] = None
                continue
        
        return music_tracks
    
    async def sync_music_video(self, video_sequences: Dict[str, str], music_tracks: Dict[str, str], arena_data: Dict) -> Dict[str, str]:
        """
        Step 7: Synchronize music with video, ensuring length matches
        """
        arena_name = arena_data['name'].lower().replace(' ', '_')
        final_dir = self.assets_path / 'final' / arena_name
        final_dir.mkdir(parents=True, exist_ok=True)
        
        final_videos = {}
        
        for video_type in video_sequences.keys():
            try:
                if video_type not in music_tracks or not music_tracks[video_type]:
                    # No music available, keep video as-is
                    final_videos[video_type] = video_sequences[video_type]
                    continue
                
                video_path = video_sequences[video_type]
                music_path = music_tracks[video_type]
                output_path = final_dir / f"{arena_name}_{video_type}_final.mp4"
                
                # Load video and audio
                video_clip = VideoFileClip(video_path)
                audio_clip = AudioFileClip(music_path)
                
                # Sync durations
                target_duration = video_clip.duration
                
                if audio_clip.duration > target_duration:
                    # Trim audio to match video
                    audio_clip = audio_clip.subclip(0, target_duration)
                elif audio_clip.duration < target_duration:
                    # Loop audio to match video duration
                    loops_needed = int(target_duration / audio_clip.duration) + 1
                    audio_clip = audio_clip.loop(n=loops_needed).subclip(0, target_duration)
                
                # Combine video and audio
                final_clip = video_clip.set_audio(audio_clip)
                
                # Export final video
                final_clip.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                
                final_videos[video_type] = str(output_path)
                logger.info(f"   Synced {video_type} video with music ({target_duration:.1f}s)")
                
                # Clean up
                video_clip.close()
                audio_clip.close()
                final_clip.close()
                
            except Exception as e:
                logger.error(f"Failed to sync {video_type} video with music: {e}")
                # Use video without music as fallback
                final_videos[video_type] = video_sequences.get(video_type)
                continue
        
        return final_videos
    
    async def create_arena_video_types(self, final_videos: Dict[str, str], arena_data: Dict) -> Dict[str, str]:
        """
        Step 8: Create all required arena video types with specific purposes
        """
        # The final_videos already contain the main types we need
        # We can create additional specialized versions if needed
        
        arena_videos = {
            'main_showcase': final_videos.get('main'),
            'intro_video': final_videos.get('intro'),
            'ambient_loop': final_videos.get('ambient'),
            'victory_celebration': final_videos.get('victory'),
            'hazard_activation': final_videos.get('hazard')
        }
        
        logger.info(f"   Created {len(arena_videos)} arena video types")
        return arena_videos
    
    async def update_arena_videos(self, arena_id: int, arena_videos: Dict[str, str]):
        """
        Update arena database record with video file paths
        """
        from shared.database.connection import SessionLocal
        from shared.models.arena import Arena, ArenaClip, ArenaClipType
        
        with SessionLocal() as session:
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            
            if arena:
                # Create ArenaClip records for each video
                clip_type_mapping = {
                    'intro_video': ArenaClipType.intro,
                    'ambient_loop': ArenaClipType.ambient,
                    'victory_celebration': ArenaClipType.victory,
                    'hazard_activation': ArenaClipType.hazard_trigger
                }
                
                for video_type, file_path in arena_videos.items():
                    if file_path and video_type in clip_type_mapping:
                        # Get video duration
                        try:
                            video_clip = VideoFileClip(file_path)
                            duration = int(video_clip.duration)
                            video_clip.close()
                        except:
                            duration = None
                        
                        # Create clip record
                        clip = ArenaClip(
                            arena_id=arena_id,
                            clip_type=clip_type_mapping[video_type],
                            file_path=file_path,
                            duration_seconds=duration,
                            resolution="1792x1024"
                        )
                        session.add(clip)
                
                session.commit()
                logger.info(f"   Updated arena {arena_id} with video paths")

# Admin Interface Integration
class ArenaCreationAPI:
    """
    API endpoints for arena creation engine
    """
    
    def __init__(self):
        self.engine = ArenaCreationEngine()
    
    async def create_arenas_endpoint(self, count: int, theme_preference: Optional[str] = None) -> Dict:
        """
        API endpoint to create multiple arenas
        """
        try:
            # Validate input
            if count < 1 or count > 100:
                return {"error": "Count must be between 1 and 100", "success": False}
            
            # Create arenas
            created_arenas = await self.engine.create_arenas_batch(count)
            
            return {
                "success": True,
                "message": f"Successfully created {len(created_arenas)} arenas",
                "arenas": created_arenas,
                "total_created": len(created_arenas)
            }
            
        except Exception as e:
            logger.error(f"Arena creation API error: {e}")
            return {"error": str(e), "success": False}

# Usage Example
async def main():
    """Example usage of the arena creation engine"""
    engine = ArenaCreationEngine()
    
    # Create 5 test arenas
    arenas = await engine.create_arenas_batch(5)
    
    print(f"Created {len(arenas)} arenas:")
    for arena in arenas:
        print(f"  🏟️ {arena['name']} ({arena['mana_color']}) - Difficulty: {arena['difficulty_rating']}/5")

if __name__ == "__main__":
    asyncio.run(main())
