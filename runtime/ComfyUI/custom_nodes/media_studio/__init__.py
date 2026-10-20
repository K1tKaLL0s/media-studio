from .speech import MediaStudioSpeech
from .pv import MediaStudioMV
from .voice_design import MediaStudioVoiceDesign
from .index_tts import MediaStudioIndexTTS25
from .ace_music import MediaStudioMusic

MediaStudioMV.GET_SCHEMA()
NODE_CLASS_MAPPINGS = {
    'MediaStudioSpeech': MediaStudioSpeech,
    'MediaStudioMV': MediaStudioMV,
    'MediaStudioVoiceDesign': MediaStudioVoiceDesign,
    'MediaStudioIndexTTS25': MediaStudioIndexTTS25,
    'MediaStudioMusic': MediaStudioMusic,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    'MediaStudioSpeech': 'Media Studio Speech',
    'MediaStudioMV': 'PV / MV Render',
    'MediaStudioVoiceDesign': 'Qwen VoiceDesign (not run)',
    'MediaStudioIndexTTS25': 'IndexTTS 2.5 (not run)',
    'MediaStudioMusic': 'ACE-Step 1.5 Music (not run)',
}
