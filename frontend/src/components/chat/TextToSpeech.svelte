<script>
  let text = "";
  let isSpeaking = false;
  let voices = [];
  let selectedVoice = null;

  // Initialize speech synthesis and get available voices
  function initSpeechSynthesis() {
    if ("speechSynthesis" in window) {
      voices = speechSynthesis.getVoices();
      selectedVoice = voices[0];

      // If voices aren't loaded immediately, wait for them
      speechSynthesis.onvoiceschanged = () => {
        voices = speechSynthesis.getVoices();
        selectedVoice = voices[0];
      };
    }
  }

  // Call initialization on component mount
  import { onMount } from "svelte";
  onMount(initSpeechSynthesis);

  function speak() {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = selectedVoice;

      utterance.onstart = () => (isSpeaking = true);
      utterance.onend = () => (isSpeaking = false);

      speechSynthesis.speak(utterance);
    } else {
      alert("Text-to-speech is not supported in your browser.");
    }
  }

  function stopSpeaking() {
    if ("speechSynthesis" in window) {
      speechSynthesis.cancel();
      isSpeaking = false;
    }
  }
</script>

<main>
  <h1>Text-to-Speech Converter</h1>

  <textarea bind:value={text} placeholder="Enter text to convert to speech"
  ></textarea>

  <select bind:value={selectedVoice}>
    {#each voices as voice}
      <option value={voice}>{voice.name} ({voice.lang})</option>
    {/each}
  </select>

  <button on:click={speak} disabled={!text || isSpeaking}>
    {isSpeaking ? "Speaking..." : "Speak"}
  </button>

  {#if isSpeaking}
    <button on:click={stopSpeaking}>Stop</button>
  {/if}
</main>

<style>
  main {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
  }

  textarea {
    width: 100%;
    height: 150px;
    margin-bottom: 10px;
  }

  select,
  button {
    margin-right: 10px;
  }
</style>
