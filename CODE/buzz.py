## -- IMPORTS

import csv;
from google.cloud import texttospeech;
from gtts import gTTS, lang;
import os;
import pyttsx3;
import sys;
import time;

## -- FUNCTIONS

def GetLogicalPath( path ) :

    return path.replace( '\\', '/' );

##

def WriteMicrosoftSpeechFile( text, voice_name, speech_file_path, pause_duration ) :

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

def WriteGoogleSpeechFile( text, language_code, speech_file_path, pause_duration ) :

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

def WriteGoogleApiSpeechFile( text, language_code, voice_name, speech_file_path, pause_duration ) :

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

def ReadTextFile( data_file_path, speech_folder_path, speech_engine_name, pause_duration ) :

    try :

        print( "Reading data :", data_file_path );

        with open( data_file_path, newline = "", encoding = "utf-8" ) as data_file :

            csv_reader = csv.reader( data_file );
            next( csv_reader );

            for row in csv_reader :

                language_code, voice_name, speech_file_name, text = row;
                speech_file_path = speech_folder_path + speech_file_name;
                print( f"Generated text speech : [{ language_code }] { text }" );

                if os.path.exists( speech_file_path ) :

                    print( "Keeping speech :", speech_file_path );

                else :

                    print( "Writing speech :", speech_file_path );

                    if speech_engine_name == "microsoft" :

                        WriteMicrosoftSpeechFile( text, voice_name, speech_file_path, pause_duration );

                    if speech_engine_name == "google" :

                        WriteGoogleSpeechFile( text, language_code, speech_file_path, pause_duration );

                    if speech_engine_name == "google-api" :

                        WriteGoogleApiSpeechFile( text, language_code, voice_name, speech_file_path, pause_duration );

    except Exception as exception :

        print( f"*** { exception }" );

## -- STATEMENTS

argument_array = sys.argv;
argument_count = len( argument_array ) - 1;

if ( argument_count == 4 ) :

    data_file_path = GetLogicalPath( argument_array[ 1 ] );
    speech_folder_path = GetLogicalPath( argument_array[ 2 ] );
    speech_engine_name = argument_array[ 3 ];
    pause_duration = float( argument_array[ 4 ] );

    if ( data_file_path.endswith( ".csv" )
         and speech_folder_path.endswith( "/" )
         and ( speech_engine_name == "microsoft"
               or speech_engine_name == "google"
               or speech_engine_name == "google-api" ) ) :

        ReadTextFile( data_file_path, speech_folder_path, speech_engine_name, pause_duration );
        sys.exit( 0 );

print( f"*** Invalid arguments : { argument_array }" );
print( "Usage: python buzz.py data.csv SPEECH_FOLDER/" );
