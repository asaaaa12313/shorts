"use client";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface Props {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

export default function FileUploader({ files, onFilesChange }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      onFilesChange([...files, ...accepted]);
    },
    [files, onFilesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "video/*": [".mp4", ".mov", ".avi", ".mkv"] },
    maxSize: 200 * 1024 * 1024,
  });

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-blue-400 bg-blue-950/30" : "border-gray-600 hover:border-gray-400"}`}
      >
        <input {...getInputProps()} />
        <div className="text-4xl mb-3">🎬</div>
        {isDragActive ? (
          <p className="text-blue-400">여기에 놓으세요!</p>
        ) : (
          <>
            <p className="text-gray-300 mb-1">영상 클립을 드래그하거나 클릭하여 업로드</p>
            <p className="text-gray-500 text-sm">MP4, MOV, AVI, MKV (파일당 200MB)</p>
          </>
        )}
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, i) => (
            <li key={i} className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2">
              <span className="text-sm text-gray-300">
                <span className="text-gray-500 mr-2">{String(i + 1).padStart(2, "0")}.</span>
                {file.name}
                <span className="text-gray-500 ml-2">({(file.size / 1024 / 1024).toFixed(1)}MB)</span>
              </span>
              <button onClick={() => removeFile(i)} className="text-red-400 hover:text-red-300 text-sm">
                삭제
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
