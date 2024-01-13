## -- IMPORTS

import csv;
import os;
import pyttsx3;
import sys;
import time;
from gtts import gTTS, lang
from google.cloud import texttospeech

## -- FUNCTIONS

def GetLogicalPath( path ) :

    return path.replace( '\\', '/' )

##

def WriteMicrosoftSpeechFile( text, voice_name, speech_file_path, pause_duration ) :

    try :

        engine = pyttsx3.init()
        microsoft_voice_list = engine.getProperty( 'voices' )

        for microsoft_voice in microsoft_voice_list :

            if voice_name in microsoft_voice.name :

                engine.setProperty( 'voice', microsoft_voice.id )
                engine.save_to_file( text, speech_file_path )
                engine.runAndWait()
                time.sleep( pause_duration )

                return

        print( f"*** Voice not found : { voice_name }" )

        for microsoft_voice in microsoft_voice_list :

            print( f"Microsoft speech voice : { microsoft_voice.name }" )

    except Exception as exception :

        print( f"*** { exception }" )

        return

##

def WriteGoogleSpeechFile( text, language_code, speech_file_path, pause_duration ) :

    try :

        google_language_name_by_code_map = lang.tts_langs().items()

        for google_language_code, language_name in google_language_name_by_code_map :

            if language_code.startswith( google_language_code ) :

                speech = gTTS( text, lang = language_code, slow = False )
                speech.save( speech_file_path )
                time.sleep( pause_duration )

                return

        print( f"*** Language code not found : { language_code }" );

        for google_language_code, google_language_name in google_language_name_by_code_map :

            print( f"Google speech language : { google_language_code } { google_language_name }" )

    except Exception as exception :

        print( f"*** { exception }" )

        return

##

def WriteGoogleApiSpeechFile( text, language_code, voice_name, speech_file_path, pause_duration ) :

    text_to_speech_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = (
        texttospeech.VoiceSelectionParams(
            language_code = language_code,
            name = voice_name
            )
        )

    audio_configuration = (
        texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
            )
        )

    try :

        response = (
            text_to_speech_client.synthesize_speech(
                input = synthesis_input,
                voice = voice,
                audio_config = audio_configuration
                )
            )

        with open( speech_file_path, 'wb' ) as speech_file :

            speech_file.write( response.audio_content )

        time.sleep( pause_duration )

    except Exception as exception :

        print( f"*** { exception }" )

        return
##

def ReadTextFile( text_file_path, speech_folder_path, pause_duration ) :

    print( f"Reading file : { text_file_path }" )

    with open( text_file_path, newline = '', encoding = 'utf-8' ) as csv_file :

        csv_reader = csv.reader( csv_file )
        next( csv_reader )

        for row in csv_reader :

            language_code, engine_name, voice_name, speech_file_name, text = row
            speech_file_path = speech_folder_path + speech_file_name

            print( f"Saying text  : [{ language_code }] { text }" )

            if os.path.exists( speech_file_path ) :

                print( f"Keeping file : { speech_file_path }" )

            else :

                print( f"Writing file : { speech_file_path }" )

                if engine_name == "Microsoft" :

                    WriteMicrosoftSpeechFile( text, voice_name, speech_file_path, pause_duration )

                if engine_name == "Google" :

                    WriteGoogleSpeechFile( text, language_code, speech_file_path, pause_duration )

                if engine_name == "GoogleApi" :

                    WriteGoogleCloudSpeechFile( text, language_code, voice_name, speech_file_path, pause_duration )

## -- STATEMENTS

if __name__ == "__main__":

    argument_list = sys.argv;

    if len( argument_list ) == 4 :

        text_file_path = GetLogicalPath( argument_list[ 1 ] )
        speech_folder_path = GetLogicalPath( argument_list[ 2 ] )
        pause_duration = float( argument_list[ 3 ] )

        if text_file_path.endswith( ".csv" ) and speech_folder_path.endswith( "/" ) :

            ReadTextFile( text_file_path, speech_folder_path, pause_duration )

            sys.exit( 0 )

    print( f"*** Invalid arguments : { argument_list }" )
    print( "Usage: python buzz.py text_file.csv SPEECH_FOLDER/" )
