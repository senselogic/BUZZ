## -- IMPORTS

import gc;
from google.cloud import texttospeech;
from gtts import gTTS, lang;
import os;
import pandas;
import pyttsx3;
import scipy;
import sys;
import time;
import torch;
from transformers import VitsModel, AutoTokenizer;
from TTS.api import TTS;

## -- FUNCTIONS

def GetLogicalPath( path ) :

    return path.replace( '\\', '/' );

##

def GetTwoLetterLanguageCode( language_code ) :

    return language_code.split( "-" )[ 0 ];

##

def GetThreeLetterLanguageCode( language_code ) :

    return (
        {
            'ar' : 'ara',    # Arabic
            'bg' : 'bul',    # Bulgarian
            'bn' : 'ben',    # Bengali
            'cs' : 'ces',    # Czech
            'da' : 'dan',    # Danish
            'de' : 'deu',    # German
            'el' : 'ell',    # Greek
            'en' : 'eng',    # English
            'es' : 'spa',    # Spanish
            'et' : 'est',    # Estonian
            'fa' : 'fas',    # Persian
            'fi' : 'fin',    # Finnish
            'fr' : 'fra',    # French
            'he' : 'heb',    # Hebrew
            'hi' : 'hin',    # Hindi
            'hr' : 'hrv',    # Croatian
            'hu' : 'hun',    # Hungarian
            'id' : 'ind',    # Indonesian
            'it' : 'ita',    # Italian
            'ja' : 'jpn',    # Japanese
            'ko' : 'kor',    # Korean
            'lt' : 'lit',    # Lithuanian
            'lv' : 'lav',    # Latvian
            'ms' : 'msa',    # Malay
            'nb' : 'nob',    # Norwegian Bokmål
            'nl' : 'nld',    # Dutch
            'pl' : 'pol',    # Polish
            'pt' : 'por',    # Portuguese
            'ro' : 'ron',    # Romanian
            'ru' : 'rus',    # Russian
            'sk' : 'slk',    # Slovak
            'sl' : 'slv',    # Slovenian
            'sr' : 'srp',    # Serbian
            'sv' : 'swe',    # Swedish
            'ta' : 'tam',    # Tamil
            'th' : 'tha',    # Thai
            'tr' : 'tur',    # Turkish
            'uk' : 'ukr',    # Ukrainian
            'vi' : 'vie',    # Vietnamese
            'zh' : 'zho'     # Chinese
        }
        ).get( GetTwoLetterLanguageCode( language_code ), "" );

##

def GenerateMicrosoftSpeechFile( text, voice_name, speech_file_path, pause_duration ) :

    engine = pyttsx3.init();
    microsoft_voice_array = engine.getProperty( 'voices' );

    for microsoft_voice in microsoft_voice_array :

        if voice_name in microsoft_voice.name :

            engine.setProperty( 'voice', microsoft_voice.id );
            engine.save_to_file( text, speech_file_path );
            engine.runAndWait();
            time.sleep( pause_duration );

            return

    print( f"*** Voice not found : { voice_name }" )

    for microsoft_voice in microsoft_voice_array :

        print( f"Available voice : { microsoft_voice.name }" );

##

def GenerateGoogleSpeechFile( text, language_code, speech_file_path, pause_duration ) :

    google_language_name_by_code_map = lang.tts_langs().items();

    for google_language_code, language_name in google_language_name_by_code_map :

        if language_code.startswith( google_language_code ) :

            speech = gTTS( text, lang = language_code, slow = False );
            speech.save( speech_file_path );
            time.sleep( pause_duration );

            return;

    print( f"*** Language code not found : { language_code }" );

    for google_language_code, google_language_name in google_language_name_by_code_map :

        print( f"Available language : { google_language_code } { google_language_name }" );

##

def GenerateGoogleApiSpeechFile( text, language_code, voice_name, speech_file_path, pause_duration ) :

    if ( "GOOGLE_API_KEY" in os.environ
         or "GOOGLE_APPLICATION_CREDENTIALS" in os.environ ) :

        text_to_speech_client = texttospeech.TextToSpeechClient();
        synthesis_input = texttospeech.SynthesisInput( text = text );

        voice = (
            texttospeech.VoiceSelectionParams(
                language_code = language_code,
                name = voice_name
                )
            );

        audio_configuration = (
            texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
                )
            );

        response = (
            text_to_speech_client.synthesize_speech(
                input = synthesis_input,
                voice = voice,
                audio_config = audio_configuration
                )
            );

        with open( speech_file_path, 'wb' ) as speech_file :

            speech_file.write( response.audio_content );

        time.sleep( pause_duration );

    else :

        print( f"*** Missing environment variable : GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS" );
        sys.exit( 0 );

##

def GenerateApiSpeechFiles( data_frame, speech_folder_path, speech_engine_name, pause_duration ) :

    for _, row in data_frame.iterrows() :

        language_code = row[ "language_code" ];
        text = row[ "text" ];
        speech_file_path = speech_folder_path + row[ "speech_file_name" ];

        print( f"Generated text speech : [{ language_code }] { text }" );

        if os.path.exists( speech_file_path ) :

            print( "Keeping speech :", speech_file_path );

        else :

            print( "Writing speech :", speech_file_path );

            if speech_engine_name == "microsoft" :

                GenerateMicrosoftSpeechFile( text, row[ "voice_name" ], speech_file_path, pause_duration );

            elif speech_engine_name == "google" :

                GenerateGoogleSpeechFile( text, language_code, speech_file_path, pause_duration );

            elif speech_engine_name == "google-api" :

                GenerateGoogleApiSpeechFile( text, language_code, row[ "voice_name" ], speech_file_path, pause_duration );

##

def GenerateMmsSpeechFiles( data_frame, speech_folder_path ) :

    data_frame = data_frame.copy().sort_values( by = "language_code", ascending = True )

    prior_language_code = "";

    for _, row in data_frame.iterrows() :

        language_code = GetThreeLetterLanguageCode( row[ "language_code" ] );
        text = row[ "text" ];
        speech_file_path = speech_folder_path + row[ "speech_file_name" ];

        print( f"Generated text speech : [{ language_code }] { text }" );

        if os.path.exists( speech_file_path ) :

            print( "Keeping speech :", speech_file_path );

        else :

            print( "Writing speech :", speech_file_path );

            if ( language_code != prior_language_code ) :

                model = VitsModel.from_pretrained( "facebook/mms-tts-" + language_code );
                tokenizer = AutoTokenizer.from_pretrained( "facebook/mms-tts-" + language_code );

                gc.collect();

            inputs = tokenizer( text, return_tensors = "pt" );

            with torch.no_grad() :

                waveform = model( **inputs ).waveform;

            scipy.io.wavfile.write(
                speech_file_path,
                rate = model.config.sampling_rate,
                data = waveform.float().numpy()
                );

##

def GenerateXttsSpeechFiles( data_frame, speech_folder_path ) :

    model = TTS( "tts_models/multilingual/multi-dataset/xtts_v2" );

    for _, row in data_frame.iterrows() :

        language_code = row[ "language_code" ];
        text = row[ "text" ];
        voice_file_path = row[ "voice_file_path" ];
        speech_file_path = speech_folder_path + row[ "speech_file_name" ];

        print( f"Generated text speech : [{ language_code }] { text }" );

        if os.path.exists( speech_file_path ) :

            print( "Keeping speech :", speech_file_path );

        else :

            print( "Writing speech :", speech_file_path );

            model.tts_to_file(
                text = text,
                file_path = speech_file_path,
                speaker_wav = voice_file_path,
                language = GetTwoLetterLanguageCode( language_code ),
                split_sentences = True
                );

##

def GenerateSpeechFiles( data_file_path, speech_folder_path, speech_engine_name, pause_duration ) :

    try :

        print( "Reading data :", data_file_path );
        data_frame = pandas.read_csv( data_file_path, na_filter = False );

        if ( speech_engine_name == "microsoft"
             or speech_engine_name == "google"
             or speech_engine_name == "google-api" ) :

            GenerateApiSpeechFiles( data_frame, speech_folder_path, speech_engine_name, pause_duration );

        elif ( speech_engine_name == "mms" ) :

            GenerateMmsSpeechFiles( data_frame, speech_folder_path );

        elif ( speech_engine_name == "xtts" ) :

            GenerateXttsSpeechFiles( data_frame, speech_folder_path );

    except Exception as exception :

        print( f"*** { exception }" );

## -- STATEMENTS

argument_array = sys.argv;
argument_count = len( argument_array ) - 1;

if ( argument_count == 3
     or argument_count == 4 ) :

    data_file_path = GetLogicalPath( argument_array[ 1 ] );
    speech_folder_path = GetLogicalPath( argument_array[ 2 ] );
    speech_engine_name = argument_array[ 3 ];

    if argument_count == 4 :

        pause_duration = float( argument_array[ 4 ] );

    else :

        pause_duration = 0;

    if ( data_file_path.endswith( ".csv" )
         and speech_folder_path.endswith( "/" )
         and ( speech_engine_name == "microsoft"
               or speech_engine_name == "google"
               or speech_engine_name == "google-api"
               or speech_engine_name == "mms"
               or speech_engine_name == "xtts" ) ) :

        GenerateSpeechFiles( data_file_path, speech_folder_path, speech_engine_name, pause_duration );

        sys.exit( 0 );

print( f"*** Invalid arguments : { argument_array }" );
print( "Usage: python buzz.py data.csv SPEECH_FOLDER/ microsoft|google|google-api|mms|xtts [<pause_duration>]" );
