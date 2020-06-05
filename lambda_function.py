import random
import requests
import json
import boto3
import ask_sdk_core
import botocore
import ast
from ask_sdk_core.utils import is_intent_name, get_dialog_state, get_slot_value
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

learningType = ""
correctWord = ""
wordChoice = ""
clueCount = 0

#hidden for security reasons- my personalized bucket name & access key information, different for everybody
bucket = '**********'
key = 'data/**********.txt'

s3 = boto3.client('s3',aws_access_key_id='*************', aws_secret_access_key='**********************')


global wordList

data = s3.get_object(Bucket='**********', Key='data/**********.txt')
filedata = data['Body'].read().decode(encoding="utf-8",errors="ignore")

for line in filedata.splitlines():
    wordList.append(line)



class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Welcome, ready to start?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class DefinitionsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DefinitionIntent")(handler_input)

    def handle(self, handler_input):
        global correctWord
        global wordPicked
        global defn
        global value
        global part
        global synonym
        global antonym
        global example

        #grabbing definitions from api that associates with the random word picked
        wordPicked = random.choice(wordList)
        url = "https://wordsapiv1.p.rapidapi.com/words/"+wordPicked
        headers = {
             'x-rapidapi-host': "wordsapiv1.p.rapidapi.com",
             'x-rapidapi-key': "c48de3a042msh2378c788ff0a427p1ac2bbjsn76cd388c2d2e"
             }
        response = requests.request("GET", url, headers=headers)
        json_data = response.json()

        #checking to make sure that the word is in the api so alexa doesn't give an error to the user

        if "results" in str(json_data):
            for item in json_data["results"]:
                defn = str(item['definition']).strip('[]')
                part = str(item['partOfSpeech']).strip('[]')
                # a sample sentence with the picked word comes as 'examples' in the api
                if 'examples' in item:
                    example = str(item['examples']).strip('[]')
                else :
                    example = "not found";
                if 'synonyms' in item:
                    synonym = str(item['synonyms']).strip('[]');
                else :
                    synonym = "not found";
                if 'antonyms' in item:
                    antonym = str(item['antonyms']).strip('[]')
                else :
                    antonym = "not found";

                value ="Definition is: "+defn+". Part of speech is "+part+". To continue, say alexa, let me guess"

        #choosing a different word in case the word is not in the api
        else:
            wordPicked = random.choice(wordList)
            url = "https://wordsapiv1.p.rapidapi.com/words/"+wordPicked
            headers = {
                'x-rapidapi-host': "wordsapiv1.p.rapidapi.com",
                'x-rapidapi-key': "c48de3a042msh2378c788ff0a427p1ac2bbjsn76cd388c2d2e"
                }
            response = requests.request("GET", url, headers=headers)
            json_data = response.json()
            for item in json_data["results"]:
                defn = str(item['definition']).strip('[]')
                part = str(item['partOfSpeech']).strip('[]')
                if 'examples' in item:
                    example = str(item['examples']).strip('[]')
                else :
                    example = "not found";
                if 'synonyms' in item:
                    synonym = str(item['synonyms']).strip('[]');
                else :
                    synonym = "not found";
                if 'antonyms' in item:
                    antonym = str(item['antonyms']).strip('[]')
                else :
                    antonym = "not found";


            value ="Definition is: "+defn+". Part of speech is "+part+". To continue, say alexa, let me guess"

        return handler_input.response_builder.speak(value).response


class AnswerIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AnswerIntent")(handler_input)
    def handle(self, handler_input):
        global wordChoice
        global clueCount
        firstClue = "the word begins with "+ wordPicked[0] + " and ends with " + wordPicked[(len(wordPicked)-1)]+". say alexa, let me guess to try again."
        secondClue= "the number of letters in the word are "+ str(len(wordPicked))+". say alexa, let me guess to try again."

        #randomizing the third clue based on what is available for each word in the api
        thirdClue=""
        if example != 'not found':
            thirdClue = "examples of the word: "+ example.replace(wordPicked, "blank")+". say alexa, let me guess to try again."
        else:
            if synonym != 'not found':
                thirdClue = "Synonyms: "+synonym+". To continue, say alexa, let me guess"
            else:
                if antonym != 'not found':
                    thirdClue = "Antonym is: "+antonym+". To continue, say alexa, let me guess"
                else:
                    thirdClue = "Sorry!I ran out of clues. The word is  "+ wordPicked +". To play more say:  alexa, next word. To end say:  alexa goodbye!"
        wordChoice = get_slot_value(handler_input=handler_input, slot_name="word")

        #if the user selected the right word

        if wordChoice == wordPicked:
            speak_output = "You selected, {}".format(wordChoice) + ". "+ "Yay! You are correct! To play more say:  alexa, next word. To end say:  alexa goodbye!"
            clueCount = 0
        else:
            #if the user requested a clue
            #only three clues are available
            if wordChoice == "clue":
                if clueCount == 0:
                    speak_output = "You requested a clue! I can give you up to three clues. "+ firstClue
                    clueCount+=1
                else:
                    if clueCount == 1:
                        speak_output = "Another clue. "+ secondClue
                        clueCount+=1
                    else:
                        if clueCount == 2:
                            speak_output = "Last Clue: "+ thirdClue
                            clueCount+=1
                        else:
                          speak_output = "Sorry! You ran out of clues. The word is  "+ wordPicked +". To play more say:  alexa, next word. To end say:  alexa goodbye!"
                          clueCount = 0
            else:
                #if the user's guess is incorrect

                if clueCount == 0:
                    speak_output = "Uh Oh... Looks like thats not correct. I can give you up to three clues. "+ firstClue
                    clueCount+=1
                else:
                    if clueCount == 1:
                        speak_output = "Whoops! Another clue. "+ secondClue
                        clueCount+=1
                    else:
                        if clueCount == 2:
                            speak_output = "Awwww! Last Clue: "+ thirdClue
                            clueCount+=1
                        else:
                          speak_output = "Sorry! Better luck next time. The word is  "+ wordPicked +". To play more say:  alexa, next word. To end say:  alexa goodbye!"
        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )

# Trial handler; Not used for final skill
class SynonymsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SynonymsIntent")(handler_input)

    def handle(self, handler_input):
        global correctWord
        global wordPicked
        global defn
        global value
        global part
        global synonym
        global antonym
        global example
        global learningType
        wordPicked = random.choice(wordList)
        url = "https://wordsapiv1.p.rapidapi.com/words/"+wordPicked
        headers = {
             'x-rapidapi-host': "wordsapiv1.p.rapidapi.com",
             'x-rapidapi-key': "c48de3a042msh2378c788ff0a427p1ac2bbjsn76cd388c2d2e"
             }
        response = requests.request("GET", url, headers=headers)
        json_data = response.json()

        for item in json_data["results"]:

            defn = str(item['definition']).strip('[]')

            if 'synonyms' in item:
                synonym = str(item['synonyms']).strip('[]');
            else :
                synonym = "not found. please say next synonym for another word";

            value ="Synonyms: "+synonym+". say let me guess to continue"
        return handler_input.response_builder.speak(value).response



# Trial handler; Not used for final skill
class AntonymsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AntonymsIntent")(handler_input)

    def handle(self, handler_input):
        global correctWord
        global wordPicked
        global defn
        global value
        global part
        global synonym
        global antonym
        global example

        wordPicked = random.choice(wordList)
        url = "https://wordsapiv1.p.rapidapi.com/words/"+wordPicked
        headers = {
             'x-rapidapi-host': "wordsapiv1.p.rapidapi.com",
             'x-rapidapi-key': "c48de3a042msh2378c788ff0a427p1ac2bbjsn76cd388c2d2e"
             }
        response = requests.request("GET", url, headers=headers)
        json_data = response.json()

        for item in json_data["results"]:

            defn = str(item['definition']).strip('[]')
            part = str(item['partOfSpeech']).strip('[]')

            if 'antonyms' in item:
                antonym = str(item['antonyms']).strip('[]')
            else :
                antonym = "not found. please say next antonym for another word.";
            value ="Antonym is: "+antonym+". To continue, say alexa, let me guess"
        return handler_input.response_builder.speak(value).response



# Trial handler; Not used for final skill
class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


# Trial handler; Not used for final skill
class SelectionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):

        return ask_utils.is_intent_name("SelectionIntent")(handler_input)
    def handle(self, handler_input):

        global learningType
        learningType = get_slot_value(handler_input=handler_input, slot_name="choice")

        if learningType:
            speak_output = "You selected, {}".format(learningType) + " "+ "Now for the next step say start definitions, synonyms, or antonyms, based on what you selected."
        else:
            speak_output = "Hello! I'm sorry, I don't yet know what choice you chose!"
        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )


class IntentReflectorHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):

    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(SelectionIntentHandler())
sb.add_request_handler(DefinitionsIntentHandler())
sb.add_request_handler(SynonymsIntentHandler())
sb.add_request_handler(AntonymsIntentHandler())
sb.add_request_handler(AnswerIntentHandler())
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
