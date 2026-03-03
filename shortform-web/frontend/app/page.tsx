"use client";
import { useState, useRef, useEffect } from "react";
import FileUploader from "@/components/FileUploader";
import DriveSearch from "@/components/DriveSearch";
import BgmSelector from "@/components/BgmSelector";
import BusinessTypeSelector from "@/components/BusinessTypeSelector";
import SubtitleEffectSelector from "@/components/SubtitleEffectSelector";
import SubtitleColorSelector from "@/components/SubtitleColorSelector";
import VoiceSelector from "@/components/VoiceSelector";
import ProgressBar from "@/components/ProgressBar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Phase = "upload" | "processing" | "done" | "error";
type SourceMode = "upload" | "drive";
type SubtitleMode = "ai" | "manual" | "none";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [activeTab, setActiveTab] = useState<"create" | "add_sub">("create");

  // --- 생성 탭 ---
  const [sourceMode, setSourceMode] = useState<SourceMode>("drive");
  const [files, setFiles] = useState<File[]>([]);
  const [driveBusiness, setDriveBusiness] = useState("");
  const [driveClipPaths, setDriveClipPaths] = useState<string[]>([]);
  const [businessName, setBusinessName] = useState("");
  const [bgmGenre, setBgmGenre] = useState("");
  const [subtitleMode, setSubtitleMode] = useState<SubtitleMode>("ai");
  const [subtitleText, setSubtitleText] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [subtitleEffect, setSubtitleEffect] = useState("");
  const [subtitleColor, setSubtitleColor] = useState("");
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [voiceId, setVoiceId] = useState("ko-KR-SunHiNeural");
  const [ttsEngine, setTtsEngine] = useState("edge");
  const [duration, setDuration] = useState(15);

  // --- 자막 입히기 탭 ---
  const [addSubFile, setAddSubFile] = useState<File | null>(null);
  const [addSubText, setAddSubText] = useState("");

  // --- 공통 ---
  const [step, setStep] = useState("");
  const [progress, setProgress] = useState(0);
  const [resultFilename, setResultFilename] = useState("");
  const [resultBgm, setResultBgm] = useState({ genre: "", filename: "" });
  const [errorMsg, setErrorMsg] = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleDriveSelect = (bizName: string, paths: string[]) => {
    setDriveBusiness(bizName);
    setDriveClipPaths(paths);
    if (!businessName) setBusinessName(bizName);
  };

  const canGenerate =
    sourceMode === "drive" ? driveClipPaths.length > 0 : files.length > 0;

  const startPolling = (taskId: string) => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/status/${taskId}`);
        const status = await res.json();
        if (status.status === "processing") {
          setStep(status.step || "");
          setProgress(status.progress || 0);
        } else if (status.status === "completed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setResultFilename(status.filename);
          setResultBgm({ genre: status.bgm_genre || "", filename: status.bgm_filename || "" });
          setProgress(100);
          setPhase("done");
        } else if (status.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setErrorMsg(status.error || "처리 중 오류가 발생했습니다");
          setPhase("error");
        }
      } catch { /* 재시도 */ }
    }, 3000);
  };

  const handleGenerate = async () => {
    setPhase("processing");
    setProgress(0);
    setStep("combining");

    try {
      let jobId = "";

      if (sourceMode === "upload") {
        const formData = new FormData();
        files.forEach((f) => formData.append("files", f));
        const uploadRes = await fetch(`${API_URL}/api/upload`, { method: "POST", body: formData });
        if (!uploadRes.ok) throw new Error("업로드 실패");
        const uploadData = await uploadRes.json();
        jobId = uploadData.job_id;
      }

      const body: Record<string, unknown> = {
        business_name: businessName || driveBusiness || "output",
        bgm_genre: bgmGenre,
        subtitle_mode: subtitleMode,
        subtitle_text: subtitleText,
        business_type: businessType,
        subtitle_effect: subtitleEffect,
        subtitle_color: subtitleColor,
        voice_enabled: voiceEnabled,
        voice_id: voiceId,
        tts_engine: ttsEngine,
        duration,
      };

      if (sourceMode === "drive") {
        body.gdrive_business = driveBusiness;
        body.gdrive_clip_paths = driveClipPaths;
      } else {
        body.job_id = jobId;
      }

      const genRes = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!genRes.ok) throw new Error("생성 요청 실패");
      const { task_id } = await genRes.json();
      startPolling(task_id);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "알 수 없는 오류");
      setPhase("error");
    }
  };

  const handleAddSubtitle = async () => {
    if (!addSubFile || !addSubText.trim()) return;
    setPhase("processing");
    setProgress(0);
    setStep("subtitles");

    try {
      const formData = new FormData();
      formData.append("file", addSubFile);
      formData.append("subtitle_text", addSubText);
      formData.append("business_name", businessName || "output");
      formData.append("subtitle_effect", subtitleEffect);
      formData.append("subtitle_color", subtitleColor);
      formData.append("voice_enabled", String(voiceEnabled));
      formData.append("voice_id", voiceId);
      formData.append("tts_engine", ttsEngine);

      const res = await fetch(`${API_URL}/api/add-subtitle`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("요청 실패");
      const { task_id } = await res.json();
      startPolling(task_id);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "알 수 없는 오류");
      setPhase("error");
    }
  };

  const handleReset = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setPhase("upload");
    setFiles([]);
    setDriveBusiness("");
    setDriveClipPaths([]);
    setBusinessName("");
    setBgmGenre("");
    setSubtitleMode("ai");
    setSubtitleText("");
    setBusinessType("");
    setSubtitleEffect("");
    setSubtitleColor("");
    setVoiceEnabled(false);
    setVoiceId("ko-KR-SunHiNeural");
    setTtsEngine("edge");
    setDuration(15);
    setProgress(0);
    setStep("");
    setResultFilename("");
    setErrorMsg("");
    setAddSubFile(null);
    setAddSubText("");
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">숏폼 자동 생성기</h1>
        <p className="text-gray-400">영상 클립으로 숏폼을 자동으로 만들어드립니다</p>
      </div>

      {phase === "upload" && (
        <>
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab("create")}
              className={`flex-1 py-2 rounded-lg text-sm font-bold transition-colors
                ${activeTab === "create" ? "bg-blue-600" : "bg-gray-800 text-gray-400"}`}
            >
              새 숏폼 만들기
            </button>
            <button
              onClick={() => setActiveTab("add_sub")}
              className={`flex-1 py-2 rounded-lg text-sm font-bold transition-colors
                ${activeTab === "add_sub" ? "bg-blue-600" : "bg-gray-800 text-gray-400"}`}
            >
              기존 영상에 자막 입히기
            </button>
          </div>

          {activeTab === "create" && (
            <div className="space-y-6">
              <section>
                <h2 className="text-lg font-semibold mb-3">1. 영상 선택</h2>
                <div className="flex gap-2 mb-3">
                  <button
                    onClick={() => setSourceMode("drive")}
                    className={`px-4 py-2 rounded-lg text-sm ${
                      sourceMode === "drive" ? "bg-blue-600" : "bg-gray-800 text-gray-300"
                    }`}
                  >
                    Google Drive에서 찾기
                  </button>
                  <button
                    onClick={() => setSourceMode("upload")}
                    className={`px-4 py-2 rounded-lg text-sm ${
                      sourceMode === "upload" ? "bg-blue-600" : "bg-gray-800 text-gray-300"
                    }`}
                  >
                    직접 업로드
                  </button>
                </div>
                {sourceMode === "drive" ? (
                  <DriveSearch onSelect={handleDriveSelect} />
                ) : (
                  <FileUploader files={files} onFilesChange={setFiles} />
                )}
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">2. 업체명</h2>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="예: 그로브반포, 코코스키간석점"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500"
                />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">3. 영상 길이</h2>
                <div className="flex gap-2">
                  {[15, 17, 20].map((d) => (
                    <button
                      key={d}
                      onClick={() => setDuration(d)}
                      className={`flex-1 py-2 rounded-lg text-sm font-bold transition-colors
                        ${duration === d ? "bg-blue-600" : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
                    >
                      {d}초
                    </button>
                  ))}
                </div>
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">4. BGM 장르</h2>
                <BgmSelector selected={bgmGenre} onSelect={setBgmGenre} />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">5. 자막</h2>
                <div className="flex gap-2 mb-3">
                  {(["ai", "manual", "none"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setSubtitleMode(mode)}
                      className={`px-4 py-2 rounded-lg text-sm ${
                        subtitleMode === mode ? "bg-blue-600" : "bg-gray-800 text-gray-300"
                      }`}
                    >
                      {{ ai: "AI 자동 생성", manual: "직접 입력", none: "자막 없이" }[mode]}
                    </button>
                  ))}
                </div>

                {subtitleMode === "ai" && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">업종을 선택하면 더 정확한 자막이 생성됩니다</p>
                    <BusinessTypeSelector selected={businessType} onSelect={setBusinessType} />
                  </div>
                )}
                {subtitleMode === "manual" && (
                  <textarea
                    value={subtitleText}
                    onChange={(e) => setSubtitleText(e.target.value)}
                    placeholder={"한 줄에 하나씩 자막을 입력하세요\n예:\n그로브 반포\n반포에서 만나는 감성 카페\n따뜻한 공간"}
                    rows={5}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500"
                  />
                )}
                {subtitleMode === "none" && (
                  <p className="text-sm text-gray-500">
                    자막 없이 영상+BGM만 합성합니다. 나중에 &quot;기존 영상에 자막 입히기&quot;로 추가할 수 있어요.
                  </p>
                )}
                {subtitleMode !== "none" && (
                  <>
                    <div className="mt-3">
                      <p className="text-sm text-gray-400 mb-2">자막 효과</p>
                      <SubtitleEffectSelector selected={subtitleEffect} onSelect={setSubtitleEffect} />
                    </div>
                    <div className="mt-3">
                      <p className="text-sm text-gray-400 mb-2">자막 색상</p>
                      <SubtitleColorSelector selected={subtitleColor} onSelect={setSubtitleColor} />
                    </div>
                    <div className="mt-3">
                      <p className="text-sm text-gray-400 mb-2">AI 음성</p>
                      <VoiceSelector
                        enabled={voiceEnabled}
                        onToggle={setVoiceEnabled}
                        voiceId={voiceId}
                        onVoiceChange={setVoiceId}
                        ttsEngine={ttsEngine}
                        onEngineChange={setTtsEngine}
                      />
                    </div>
                  </>
                )}
              </section>

              <button
                onClick={handleGenerate}
                disabled={!canGenerate}
                className={`w-full py-3 rounded-xl text-lg font-bold transition-colors
                  ${canGenerate ? "bg-blue-600 hover:bg-blue-500" : "bg-gray-700 text-gray-500 cursor-not-allowed"}`}
              >
                숏폼 만들기
              </button>
            </div>
          )}

          {activeTab === "add_sub" && (
            <div className="space-y-6">
              <section>
                <h2 className="text-lg font-semibold mb-3">1. 영상 업로드</h2>
                <p className="text-xs text-yellow-400/70 mb-3">원본 영상에 이미 자막이 있는 경우 새 자막과 겹칠 수 있습니다</p>
                <label className={`block w-full border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
                  ${addSubFile ? "border-purple-500 bg-purple-600/10" : "border-gray-600 hover:border-gray-500 bg-gray-800/50"}`}>
                  <input
                    type="file"
                    accept="video/*"
                    className="hidden"
                    onChange={(e) => setAddSubFile(e.target.files?.[0] || null)}
                  />
                  {addSubFile ? (
                    <div>
                      <video
                        src={URL.createObjectURL(addSubFile)}
                        className="w-full max-w-xs mx-auto rounded-lg mb-3"
                        style={{ aspectRatio: "9/16", maxHeight: "200px", objectFit: "cover" }}
                        muted
                        preload="metadata"
                      />
                      <p className="text-sm text-gray-300">{addSubFile.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{(addSubFile.size / 1024 / 1024).toFixed(1)}MB</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-gray-400 text-sm">클릭하여 영상 파일을 선택하세요</p>
                      <p className="text-gray-500 text-xs mt-1">MP4, MOV 등</p>
                    </div>
                  )}
                </label>
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">2. 자막 입력</h2>
                <textarea
                  value={addSubText}
                  onChange={(e) => setAddSubText(e.target.value)}
                  placeholder={"한 줄에 하나씩 자막을 입력하세요\n예:\n그로브 반포\n감성 카페\n지금 방문하세요!"}
                  rows={5}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500"
                />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">3. 자막 효과</h2>
                <SubtitleEffectSelector selected={subtitleEffect} onSelect={setSubtitleEffect} />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">4. 자막 색상</h2>
                <SubtitleColorSelector selected={subtitleColor} onSelect={setSubtitleColor} />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">5. AI 음성</h2>
                <VoiceSelector
                  enabled={voiceEnabled}
                  onToggle={setVoiceEnabled}
                  voiceId={voiceId}
                  onVoiceChange={setVoiceId}
                  ttsEngine={ttsEngine}
                  onEngineChange={setTtsEngine}
                />
              </section>

              <section>
                <h2 className="text-lg font-semibold mb-3">6. 업체명 (선택)</h2>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="파일명에 사용됩니다"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500"
                />
              </section>

              <button
                onClick={handleAddSubtitle}
                disabled={!addSubFile || !addSubText.trim()}
                className={`w-full py-3 rounded-xl text-lg font-bold transition-colors
                  ${addSubFile && addSubText.trim()
                    ? "bg-purple-600 hover:bg-purple-500"
                    : "bg-gray-700 text-gray-500 cursor-not-allowed"}`}
              >
                자막 입히기
              </button>
            </div>
          )}

        </>
      )}

      {phase === "processing" && (
        <div className="bg-gray-900 rounded-2xl p-8">
          <h2 className="text-xl font-bold mb-6 text-center">영상을 만들고 있어요</h2>
          <ProgressBar step={step} progress={progress} />
          <p className="text-center text-gray-500 text-sm mt-6">약 2~3분 소요됩니다</p>
        </div>
      )}

      {phase === "done" && resultFilename && (
        <div className="bg-gray-900 rounded-2xl p-8 text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-xl font-bold mb-2">완성되었어요!</h2>
          {resultBgm.genre && (
            <p className="text-gray-400 text-sm mb-6">BGM: {resultBgm.genre} - {resultBgm.filename}</p>
          )}
          <video
            src={`${API_URL}/api/download/${resultFilename}`}
            controls
            className="w-full max-w-xs mx-auto rounded-xl mb-6"
            style={{ aspectRatio: "9/16" }}
          />
          <div className="flex gap-3 justify-center">
            <a
              href={`${API_URL}/api/download/${resultFilename}`}
              download
              className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-xl font-bold"
            >
              다운로드
            </a>
            <button onClick={handleReset} className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-xl font-bold">
              다시 만들기
            </button>
          </div>
        </div>
      )}

      {phase === "error" && (
        <div className="bg-gray-900 rounded-2xl p-8 text-center">
          <div className="text-5xl mb-4">😥</div>
          <h2 className="text-xl font-bold mb-2">오류가 발생했어요</h2>
          <p className="text-red-400 text-sm mb-6">{errorMsg}</p>
          <button onClick={handleReset} className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-xl font-bold">
            다시 시도
          </button>
        </div>
      )}
    </div>
  );
}
