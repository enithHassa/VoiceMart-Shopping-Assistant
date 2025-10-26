import { useEffect, useRef } from "react";
import { useMediaRecorder } from "../lib/recorder";

type Props = {
  onComplete: (file: File) => void; // called when user stops and we have a blob
  onTranscript?: (text: string) => void; // called when we get a transcript
  autoSend?: boolean;               // if true, auto fire onComplete on stop
  label?: string;
  disabled?: boolean;
};

export default function VoiceRecorder({ onComplete, onTranscript, label = "Hold to talk", disabled = false }: Props) {
  const { 
    isRecording, 
    recordingTime, 
    transcript,
    isProcessing,
    error,
    startRecording, 
    stopRecording, 
    resetRecording, 
    hasPermission 
  } = useMediaRecorder({
    onTranscript: (text) => {
      onTranscript?.(text);
    }
  });
  const MIN_RECORDING_SECONDS = 1; // Minimum 1 second of recording
  const isMouseDownRef = useRef(false);

  // Add global listeners to handle mouse up outside the button
  // Remove global event listeners that were causing immediate stopping
  // useEffect(() => {
  //   const handleGlobalMouseUp = () => {
  //     if (isMouseDownRef.current && isRecording) {
  //       console.log("🖱️ Global mouse up - stopping recording");
  //       stop();
  //       isMouseDownRef.current = false;
  //     }
  //   };

  //   const handleGlobalTouchEnd = () => {
  //     if (isMouseDownRef.current && isRecording) {
  //       console.log("👆 Global touch end - stopping recording");
  //       stop();
  //       isMouseDownRef.current = false;
  //     }
  //   };

  //   document.addEventListener("mouseup", handleGlobalMouseUp);
  //   document.addEventListener("touchend", handleGlobalTouchEnd);

  //   return () => {
  //     document.removeEventListener("mouseup", handleGlobalMouseUp);
  //     document.removeEventListener("touchend", handleGlobalTouchEnd);
  //   };
  // }, [isRecording, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      resetRecording();
    };
  }, [resetRecording]);

  const handleMouseDown = (e: React.MouseEvent) => {
    console.log("🖱️ Mouse down event");
    e.preventDefault();
    e.stopPropagation();
    isMouseDownRef.current = true;
    if (!disabled && !isRecording) {
      console.log("🎤 Starting voice recording...");
      startRecording();
    } else {
      console.log("⚠️ Cannot start:", { disabled, isRecording });
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    console.log("🖱️ Mouse up event");
    console.log("🖱️ Current state:", { isRecording, recordingTime, MIN_RECORDING_SECONDS });
    e.preventDefault();
    e.stopPropagation();
    isMouseDownRef.current = false;
    if (isRecording) {
      console.log("🎤 Stopping voice recording...");
      stopRecording();
    } else {
      console.log("⚠️ Not recording, ignoring mouse up");
    }
  };

  const handleMouseLeave = (e: React.MouseEvent) => {
    e.preventDefault();
    if (isRecording) stopRecording();
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    console.log("👆 Touch start event");
    e.preventDefault();
    e.stopPropagation();
    isMouseDownRef.current = true;
    if (!disabled && !isRecording) {
      console.log("🎤 Starting voice recording (touch)...");
      startRecording();
    } else {
      console.log("⚠️ Cannot start (touch):", { disabled, isRecording });
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    console.log("👆 Touch end event");
    console.log("👆 Current state:", { isRecording, recordingTime, MIN_RECORDING_SECONDS });
    e.preventDefault();
    e.stopPropagation();
    isMouseDownRef.current = false;
    if (isRecording) {
      console.log("🎤 Stopping voice recording (touch)...");
      stopRecording();
    } else {
      console.log("⚠️ Not recording (touch), ignoring touch end");
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div className="flex items-center gap-3">
      <button
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onClick={handleClick}
        type="button"
        disabled={disabled}
        className={`w-14 h-14 rounded-full flex items-center justify-center shadow transition-all duration-200 ${
          disabled 
            ? "bg-gray-400 cursor-not-allowed" 
            : isRecording 
              ? "bg-red-600 animate-pulse hover:bg-red-700" 
              : "bg-blue-600 hover:bg-blue-700"
        } text-white select-none`}
        title={disabled ? "Voice search disabled" : label}
      >
        {isRecording ? "●" : "🎤"}
      </button>

      <div className="text-sm">
        <div className="font-medium">{label}</div>
        <div className="text-gray-600">
          {disabled 
            ? "Voice search disabled" 
            : isRecording 
              ? `Recording… ${recordingTime}s` 
              : isProcessing
                ? "Processing speech..."
                : "Click & hold to record"
          }
        </div>
        {transcript && !isProcessing && (
          <div className="text-green-600 text-xs mt-1 max-w-64">
            "{transcript}"
          </div>
        )}
        {error && (
          <div className="text-red-600 text-xs mt-1 max-w-64">
            {error}
          </div>
        )}
        {hasPermission === false && <div className="text-red-600 text-xs">Microphone permission denied</div>}
      </div>

      {isRecording && (
        <button
          className="ml-2 text-xs px-2 py-1 rounded bg-gray-200 hover:bg-gray-300 transition-colors"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            resetRecording();
          }}
          type="button"
        >
          Cancel
        </button>
      )}
    </div>
  );
}