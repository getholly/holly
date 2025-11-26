<script lang="ts">
  import { tick, getContext, createEventDispatcher } from "svelte";
  import { settings, prompt } from "$lib/store/chat/chat.store";
  import { transcribeAudio } from "$lib/store/audio";
  import { blobToFile } from "$lib/utils/macUtils";
  import Tooltip from "$components/chat/Tooltip.svelte";
  //export let submitPrompt: Function;

  export let speechRecognitionEnabled = true;
  const dispatch = createEventDispatcher();
  const i18n = getContext("i18n");
  let audioChunks = [];
  let isRecording = false;
  let mediaRecorder;
  const MIN_DECIBELS = -45;
  let speechRecognition;
  const speechRecognitionHandler = () => {
    // Check if SpeechRecognition is supported
    prompt.set("");
    if (isRecording) {
      if (speechRecognition) {
        speechRecognition.stop();
      }

      if (mediaRecorder) {
        mediaRecorder.stop();
      }
    } else {
      isRecording = true;

      //if ($settings?.audio?.STTEngine ?? '' !== '') {
      if ($settings?.audio) {
        startRecording();
      } else {
        if (
          "SpeechRecognition" in window ||
          "webkitSpeechRecognition" in window
        ) {
          // Create a SpeechRecognition object
          speechRecognition = new (window.SpeechRecognition ||
            window.webkitSpeechRecognition)();

          // Set continuous to true for continuous recognition
          speechRecognition.continuous = true;

          // Set the timeout for turning off the recognition after inactivity (in milliseconds)
          const inactivityTimeout = 3000; // 3 seconds

          let timeoutId;
          // Start recognition
          speechRecognition.start();

          // Event triggered when speech is recognized
          speechRecognition.onresult = async (event) => {
            // Clear the inactivity timeout
            clearTimeout(timeoutId);

            // Handle recognized speech
            console.log(event);
            const transcript =
              event.results[Object.keys(event.results).length - 1][0]
                .transcript;

            prompt.set(`${$prompt} ${transcript}`);

            await tick();

            // Restart the inactivity timeout
            timeoutId = setTimeout(() => {
              console.log("Speech recognition turned off due to inactivity.");
              speechRecognition.stop();
            }, inactivityTimeout);
          };

          // Event triggered when recognition is ended
          speechRecognition.onend = function () {
            // Restart recognition after it ends
            console.log("recognition ended");
            isRecording = false;
            //if (prompt !== '' && $settings?.speechAutoSend === true) {
            console.log(`TODO: submit Prompt: ${$prompt}`);
            // talkToTutor($sessionInfo.session_id, $prompt)
            // todo - send to backend -> send $prompt (send message api)
            dispatch("sendChatMessage");
          };

          // Event triggered when an error occurs
          speechRecognition.onerror = function (event) {
            console.log(event);
            updateStatus(
              $i18n.t(`Speech recognition error: {{error}}`, {
                error: event.error,
              }),
            );
            isRecording = false;
          };
        } else {
          updateStatus(
            $i18n.t("SpeechRecognition API is not supported in this browser."),
          );
        }
      }
    }
  };
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.onstart = () => {
      isRecording = true;
      console.log("Recording started");
    };
    mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
    mediaRecorder.onstop = async () => {
      isRecording = false;
      console.log("Recording stopped");

      // Create a blob from the audio chunks
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

      const file = blobToFile(audioBlob, "recording.wav");

      const res = await transcribeAudio(localStorage.token, file).catch(
        (error) => {
          console.error(`transcribe audio: ${error}`);
          return null;
        },
      );

      if (res) {
        let txt_prompt = res.text;
        await tick();
        console.log(`TODO: submit Prompt2: ${txt_prompt}`);
      }

      // saveRecording(audioBlob);
      audioChunks = [];
    };

    // Start recording
    mediaRecorder.start();

    // Monitor silence
    monitorSilence(stream);
  };

  const monitorSilence = (stream) => {
    const audioContext = new AudioContext();
    const audioStreamSource = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.minDecibels = MIN_DECIBELS;
    audioStreamSource.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    const domainData = new Uint8Array(bufferLength);

    let lastSoundTime = Date.now();

    const detectSound = () => {
      analyser.getByteFrequencyData(domainData);

      if (domainData.some((value) => value > 0)) {
        lastSoundTime = Date.now();
      }

      if (isRecording && Date.now() - lastSoundTime > 3000) {
        mediaRecorder.stop();
        audioContext.close();
        return;
      }

      window.requestAnimationFrame(detectSound);
    };

    window.requestAnimationFrame(detectSound);
  };
</script>

<Tooltip content={""}>
  {#if speechRecognitionEnabled}
    <button
      id="voice-input-button"
      class=" text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-full p-1.5 mr-0.5 self-center dark:hover:bg-gray-800"
      type="button"
      on:click={() => {
        speechRecognitionHandler();
      }}
    >
      {#if isRecording}
        <svg
          class=" w-5 h-5 translate-y-[0.5px]"
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <style>
            .spinner_qM83 {
              animation: spinner_8HQG 1.05s infinite;
            }

            .spinner_oXPr {
              animation-delay: 0.1s;
            }

            .spinner_ZTLf {
              animation-delay: 0.2s;
            }

            @keyframes spinner_8HQG {
              0%,
              57.14% {
                animation-timing-function: cubic-bezier(0.33, 0.66, 0.66, 1);
                transform: translate(0);
              }
              28.57% {
                animation-timing-function: cubic-bezier(0.33, 0, 0.66, 0.33);
                transform: translateY(-6px);
              }
              100% {
                transform: translate(0);
              }
            }
          </style>
          <circle class="spinner_qM83" cx="4" cy="12" r="2.5" />
          <circle class="spinner_qM83 spinner_oXPr" cx="12" cy="12" r="2.5" />
          <circle class="spinner_qM83 spinner_ZTLf" cx="20" cy="12" r="2.5" />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5 translate-y-[0.5px]"
        >
          <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
          <path
            d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z"
          />
        </svg>
      {/if}
    </button>
  {/if}
</Tooltip>
