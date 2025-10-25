import { useRef, useState } from "react";

type Props = {
  onPickFile: (file: File) => void;
  accept?: string;
};

export default function VoiceButton({ onPickFile, accept = "audio/*" }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);

  const handleClick = () => inputRef.current?.click();

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      setBusy(true);
      onPickFile(f);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        className="px-4 py-3 rounded-xl border bg-white"
        title="Upload an audio file to search"
        disabled={busy}
      >
        {busy ? "Uploading…" : "🎤 Voice"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handleChange}
      />
    </>
  );
}
