import { useEffect, useRef, useState } from "react";

type MelodyNote = {
  frequency: number;
  beats: number;
};

const BEAT_SECONDS = 0.62;

// A gentle, music-box-style phrase inspired by the public-domain melody
// "Silent Night". Generating it in the browser keeps the app self-contained.
const MELODY: MelodyNote[] = [
  { frequency: 392.0, beats: 1.5 },
  { frequency: 440.0, beats: 0.5 },
  { frequency: 392.0, beats: 1 },
  { frequency: 329.63, beats: 2 },
  { frequency: 392.0, beats: 1.5 },
  { frequency: 440.0, beats: 0.5 },
  { frequency: 392.0, beats: 1 },
  { frequency: 329.63, beats: 2 },
  { frequency: 587.33, beats: 2 },
  { frequency: 587.33, beats: 1 },
  { frequency: 493.88, beats: 2 },
  { frequency: 523.25, beats: 2 },
  { frequency: 523.25, beats: 1 },
  { frequency: 392.0, beats: 2 },
  { frequency: 440.0, beats: 2 },
  { frequency: 440.0, beats: 1 },
  { frequency: 523.25, beats: 1.5 },
  { frequency: 493.88, beats: 0.5 },
  { frequency: 440.0, beats: 1 },
  { frequency: 392.0, beats: 1.5 },
  { frequency: 440.0, beats: 0.5 },
  { frequency: 392.0, beats: 1 },
  { frequency: 329.63, beats: 2 },
];

function scheduleMelody(audioContext: AudioContext) {
  let noteStart = audioContext.currentTime + 0.08;

  MELODY.forEach(({ frequency, beats }) => {
    const noteLength = beats * BEAT_SECONDS;
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, noteStart);

    gain.gain.setValueAtTime(0.0001, noteStart);
    gain.gain.exponentialRampToValueAtTime(0.045, noteStart + 0.04);
    gain.gain.exponentialRampToValueAtTime(
      0.0001,
      noteStart + Math.max(0.12, noteLength - 0.04),
    );

    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start(noteStart);
    oscillator.stop(noteStart + noteLength);

    noteStart += noteLength;
  });

  return Math.max(0, (noteStart - audioContext.currentTime) * 1000);
}

function ChristmasMusic() {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const loopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopMusic = () => {
    if (loopTimerRef.current) {
      clearTimeout(loopTimerRef.current);
      loopTimerRef.current = null;
    }

    if (audioContextRef.current) {
      void audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsPlaying(false);
  };

  const startMusic = async () => {
    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;
    await audioContext.resume();

    const playLoop = () => {
      if (audioContext.state === "closed") return;

      const melodyLength = scheduleMelody(audioContext);
      loopTimerRef.current = setTimeout(playLoop, melodyLength + 900);
    };

    playLoop();
    setIsPlaying(true);
  };

  const toggleMusic = () => {
    if (isPlaying) {
      stopMusic();
      return;
    }

    void startMusic();
  };

  useEffect(() => stopMusic, []);

  return (
    <div className="mt-auto rounded-2xl border border-pink-100 bg-pink-50/70 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-pink-400">
        Christmas ambience
      </p>
      <button
        type="button"
        onClick={toggleMusic}
        aria-pressed={isPlaying}
        aria-label={isPlaying ? "Pause Christmas music" : "Play Christmas music"}
        className="flex w-full items-center justify-between rounded-xl bg-white px-3 py-2 text-sm font-medium text-stone-700 shadow-sm transition hover:bg-pink-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
      >
        <span>{isPlaying ? "Soft music playing" : "Play soft music"}</span>
        <span aria-hidden="true">{isPlaying ? "❚❚" : "♪"}</span>
      </button>
    </div>
  );
}

export default ChristmasMusic;
