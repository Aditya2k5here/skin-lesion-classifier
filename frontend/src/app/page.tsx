"use client";
/* eslint-disable @next/next/no-img-element */

import { useState, useRef, useCallback, type ChangeEvent, type DragEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud, Camera, X, Zap, CheckCircle2, AlertTriangle,
  ArrowRight, RotateCcw, Stethoscope, Microscope, ShieldCheck
} from "lucide-react";

const easing = "easeOut";

type PredictionResult = {
  class_id?: string;
  confidence?: number;
  name?: string;
  description?: string;
  cause?: string;
  cure?: string;
  error?: string;
} | null;

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PredictionResult>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [modelLoaded, setModelLoaded] = useState<boolean | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  /* ─── Drag & Drop ─── */
  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); e.stopPropagation(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFileSelection(e.dataTransfer.files[0]);
  };
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFileSelection(e.target.files[0]);
  };
  const handleFileSelection = (f: File) => {
    if (!f.type.startsWith("image/")) return;
    setFile(f); setPreviewUrl(URL.createObjectURL(f)); setResult(null); setShowResult(false); closeCamera();
  };

  /* ─── Camera ─── */
  const startCamera = async () => {
    setResult(null); setIsCameraOpen(true); setPreviewUrl(null); setFile(null); setShowResult(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch { setIsCameraOpen(false); }
  };
  const closeCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsCameraOpen(false);
  }, []);
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current, c = canvasRef.current;
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d")?.drawImage(v, 0, 0, c.width, c.height);
    c.toBlob(blob => {
      if (blob) handleFileSelection(new File([blob], "capture.jpg", { type: "image/jpeg" }));
    }, "image/jpeg");
  };

  /* ─── Analysis ─── */
  const analyzeImage = async () => {
    if (!file) return;
    setIsAnalyzing(true); setResult(null); setShowResult(false);
    const fd = new FormData(); fd.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/analyze", { method: "POST", body: fd });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setModelLoaded(data.model_loaded ?? null);
      setResult(data.prediction);
      setTimeout(() => setShowResult(true), 100);
    } catch {
      setResult({ error: "Unable to reach the analysis engine. Please ensure the backend is running." });
      setTimeout(() => setShowResult(true), 100);
    } finally { setIsAnalyzing(false); }
  };

  const clearAll = () => {
    setFile(null); setPreviewUrl(null); setResult(null); setShowResult(false); closeCamera();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  /* ─── View States ─── */
  const isIdle = !file && !isCameraOpen && !result;
  const hasImage = !!previewUrl;
  const hasResult = !!result && !result.error && showResult;
  const hasError = !!result?.error && showResult;
  const confidence = result?.confidence ? Math.round(result.confidence * 100) : 0;

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden" style={{ background: "var(--bg)" }}>
      {/* Grid overlay */}
      <div className="fixed inset-0 pointer-events-none z-0" style={{
        backgroundImage: "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
        backgroundSize: "60px 60px"
      }} />

      {/* Main content */}
      <main className="relative z-10 flex flex-col items-center justify-center flex-1 px-6 py-16 md:py-20">

        {/* ─── Hero Text ─── */}
        <motion.div
          className="text-center mb-12 md:mb-16"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0, duration: 0.5, ease: easing }}
            className="flex items-center justify-center gap-2 mb-6"
          >
            <span className="tag">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] inline-block" />
              AI Dermatology
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08, duration: 0.5, ease: easing }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-semibold leading-[1.05] tracking-tight mb-6"
          >
            <span className="text-gradient">Understand</span>
            <br />
            <span style={{ color: "var(--text-primary)" }}>your skin.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.16, duration: 0.5, ease: easing }}
            className="text-lg md:text-xl max-w-lg mx-auto leading-relaxed"
            style={{ color: "var(--text-secondary)" }}
          >
            Neural-powered dermatology in seconds. Upload a photo and get an instant AI clinical report.
          </motion.p>
        </motion.div>

        {/* ─── Core Interactive Area ─── */}
        <AnimatePresence mode="wait">

          {/* IDLE: Upload / Camera CTA */}
          {isIdle && !isAnalyzing && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.3, duration: 0.5, ease: [0.22, 1, 0.36, 1] } }}
              exit={{ opacity: 0, y: -16, transition: { duration: 0.2 } }}
              className="w-full"
              style={{ maxWidth: 520 }}
            >
              {/* Drop Zone */}
              <div
                onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`cursor-pointer transition-all duration-300 flex flex-col items-center justify-center gap-4 p-12 mb-5 ${dragActive ? "glass-active" : ""}`}
                style={{
                  borderRadius: 28,
                  minHeight: 240,
                  background: dragActive ? "var(--accent-glow)" : "rgba(255,255,255,0.04)",
                  border: `1px solid ${dragActive ? "rgba(99,202,255,0.5)" : "rgba(255,255,255,0.08)"}`,
                  backdropFilter: "blur(20px)",
                  WebkitBackdropFilter: "blur(20px)",
                  boxShadow: dragActive ? "0 0 40px var(--accent-glow)" : "none",
                }}
              >
                <input ref={fileInputRef} type="file" accept="image/*" onChange={handleChange} className="hidden" />
                <motion.div
                  animate={{ y: dragActive ? -6 : 0 }} transition={{ type: "spring", stiffness: 300 }}
                  className="w-16 h-16 flex items-center justify-center rounded-2xl"
                  style={{ background: "var(--accent-glow)", border: "1px solid rgba(99,202,255,0.2)" }}
                >
                  <UploadCloud className="w-7 h-7" style={{ color: "var(--accent)" }} />
                </motion.div>
                <div className="text-center">
                  <p className="text-base font-medium mb-1" style={{ color: "var(--text-primary)" }}>
                    {dragActive ? "Drop to analyse" : "Drop your image here"}
                  </p>
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>or click to browse files</p>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex gap-3" style={{ overflow: "hidden" }}>
                <button className="btn-primary" style={{ flex: 1, minWidth: 0 }} onClick={() => fileInputRef.current?.click()}>
                  <UploadCloud className="w-4 h-4" style={{ flexShrink: 0 }} />
                  Upload Photo
                </button>
                <button className="btn-secondary" style={{ flex: 1, minWidth: 0 }} onClick={startCamera}>
                  <Camera className="w-4 h-4" style={{ flexShrink: 0 }} />
                  Use Camera
                </button>
              </div>

              {/* Feature pills */}
              <div className="flex flex-wrap justify-center gap-3 mt-8">
                {[
                  { icon: <Microscope className="w-3.5 h-3.5" />, label: "CNN Powered" },
                  { icon: <ShieldCheck className="w-3.5 h-3.5" />, label: "Private & Secure" },
                  { icon: <Zap className="w-3.5 h-3.5" />, label: "Instant Results" },
                ].map((f, i) => (
                  <span key={i} className="tag" style={{ color: "var(--text-secondary)" }}>
                    <span style={{ color: "var(--accent)" }}>{f.icon}</span>
                    {f.label}
                  </span>
                ))}
              </div>
            </motion.div>
          )}

          {/* CAMERA VIEW */}
          {isCameraOpen && !previewUrl && (
            <motion.div
              key="camera"
              initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.3 }}
              className="glass overflow-hidden mb-5 flex-shrink-0"
              style={{ borderRadius: 28, width: "100%", maxWidth: 400 }}
            >
              <div className="relative w-full" style={{ height: 300 }}>
                <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                <canvas ref={canvasRef} className="hidden" />
                {/* Live badge */}
                <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(8px)" }}>
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-xs font-semibold text-white tracking-widest">LIVE</span>
                </div>
                {/* Close */}
                <button onClick={closeCamera} className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full"
                  style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(8px)", color: "white", border: "none", cursor: "pointer" }}>
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="p-5 flex gap-3">
                <button className="btn-secondary flex-1" onClick={closeCamera}>Cancel</button>
                <button className="btn-primary flex-1" onClick={capturePhoto}>
                  <Camera className="w-4 h-4" /> Capture
                </button>
              </div>
            </motion.div>
          )}

          {/* IMAGE SELECTED: Preview + Analyse */}
          {hasImage && !isAnalyzing && !result && (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.35 }}
              className="flex-shrink-0"
              style={{ width: "100%", maxWidth: 400 }}
            >
              <motion.div layoutId="photo-wrapper" className="glass overflow-hidden mb-5 w-full" style={{ borderRadius: 28 }}>
                <div className="relative w-full" style={{ height: 300, display: "flex" }}>
                  <img src={previewUrl!} alt="Skin sample" className="absolute inset-0 w-full h-full object-cover" />
                  {/* Re-select & clear */}
                  <div className="absolute inset-0 flex items-end p-5 gap-2"
                    style={{ background: "linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 50%)" }}>
                    <button onClick={clearAll} className="btn-secondary text-xs px-4 py-2.5" style={{ borderRadius: 99, color: "white", borderColor: "rgba(255,255,255,0.25)" }}>
                      <RotateCcw className="w-3.5 h-3.5" /> Change image
                    </button>
                  </div>
                </div>
              </motion.div>
              <button className="btn-primary w-full text-base py-5" onClick={analyzeImage}
                style={{ borderRadius: 99, fontSize: 16 }}>
                <Zap className="w-5 h-5" />
                Analyse Skin
                <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}

          {/* ANALYSING */}
          {isAnalyzing && (
            <motion.div
              key="analysing"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex-shrink-0"
              style={{ width: "100%", maxWidth: 400 }}
            >
              <motion.div layoutId="photo-wrapper" className="glass overflow-hidden mb-5 w-full" style={{ borderRadius: 28 }}>
                <div className="relative w-full" style={{ height: 300, display: "flex" }}>
                  {previewUrl && <img src={previewUrl!} alt="Skin sample" className="absolute inset-0 w-full h-full object-cover" style={{ opacity: 0.6 }} />}
                  {/* Scan line animation */}
                  <div className="scan-line" />
                  {/* Center loader */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                    <div className="w-16 h-16 rounded-full flex items-center justify-center"
                      style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(12px)", border: "1px solid rgba(99,202,255,0.3)" }}>
                      <div className="w-7 h-7 rounded-full border-2 animate-spin"
                        style={{ borderColor: "rgba(99,202,255,0.2)", borderTopColor: "var(--accent)" }} />
                    </div>
                    <div className="text-center">
                      <p className="font-semibold text-white mb-1">Analysing tissue patterns</p>
                      <p className="text-sm" style={{ color: "rgba(255,255,255,0.5)" }}>Running deep neural inference…</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* ERROR STATE */}
          {hasError && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="w-full glass p-8 text-center"
              style={{ borderRadius: 28, borderColor: "rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.06)", maxWidth: 520 }}
            >
              <AlertTriangle className="w-12 h-12 mx-auto mb-4" style={{ color: "#ef4444" }} />
              <h3 className="text-xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Connection Failed</h3>
              <p className="text-sm leading-relaxed mb-6" style={{ color: "var(--text-secondary)" }}>{result?.error}</p>
              <button className="btn-secondary mx-auto" onClick={clearAll}>
                <RotateCcw className="w-4 h-4" /> Try Again
              </button>
            </motion.div>
          )}

          {/* ─── RESULT PANEL ─── */}
          {hasResult && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              style={{
                width: "100%",
                maxWidth: 1000,
                display: "flex",
                flexWrap: "wrap",
                gap: "32px",
                alignItems: "flex-start",
                justifyContent: "center"
              }}
            >
              {/* Left Column: Image */}
              <div style={{ width: "100%", maxWidth: 400, flexShrink: 0 }}>
                <motion.div layoutId="photo-wrapper" className="glass overflow-hidden w-full" style={{ borderRadius: 28 }}>
                  <div style={{ position: "relative", width: "100%", height: 300, display: "flex" }}>
                    {previewUrl && (
                      <img src={previewUrl!} alt="Sample" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                    )}
                  </div>
                </motion.div>

                <div className="mt-5 flex gap-3">
                  <button className="btn-secondary w-full" onClick={clearAll}>
                    <RotateCcw className="w-4 h-4" /> New Analysis
                  </button>
                </div>
                <p className="text-center text-xs mt-5 leading-relaxed" style={{ color: "rgba(240,244,255,0.3)" }}>
                  <strong className="font-semibold" style={{ color: "rgba(240,244,255,0.45)" }}>Educational use only.</strong><br />
                  This is a CNN estimation, not a clinical diagnosis. Consult a registered dermatologist.
                </p>
              </div>

              {/* Right Column: Data */}
              <div style={{ flex: "1 1 400px", minWidth: 0, display: "flex", flexDirection: "column" }}>
                {modelLoaded === false && (
                  <div className="mb-4 p-4 rounded-xl flex items-start gap-3" style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: "#ef4444", marginTop: 2 }} />
                    <div>
                      <h4 className="text-sm font-semibold mb-1" style={{ color: "#ef4444" }}>Model Not Trained</h4>
                      <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                        The backend does not have a trained model loaded (`best_model.pth` is missing). It is currently running in a fallback mode. To fix this, train the model with your dataset.
                      </p>
                    </div>
                  </div>
                )}

                <div className="glass p-6 mb-4" style={{ borderRadius: 28 }}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="tag" style={{ borderColor: "rgba(99,202,255,0.3)", color: "var(--accent)" }}>
                      <CheckCircle2 className="w-3 h-3" /> Diagnosis Complete
                    </span>
                  </div>
                  <h2 className="text-3xl md:text-3xl lg:text-4xl font-semibold leading-tight mb-2" style={{ color: "var(--text-primary)" }}>
                    {result?.name}
                  </h2>

                  <div className="flex items-center gap-3 mt-4 mb-6">
                    <div className="confidence-bar-track flex-1">
                      <motion.div
                        className="confidence-bar-fill"
                        initial={{ width: "0%" }}
                        animate={{ width: `${confidence}%` }}
                        transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
                      />
                    </div>
                    <span className="text-xs font-bold font-mono" style={{ color: "var(--accent)", flexShrink: 0 }}>
                      {confidence}% CONFIDENCE
                    </span>
                  </div>

                  <p className="text-xs font-semibold tracking-widest uppercase mb-2" style={{ color: "var(--text-secondary)" }}>
                    Clinical Description
                  </p>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(240,244,255,0.75)" }}>{result?.description}</p>
                </div>

                <div className="glass p-6 mb-4" style={{ borderRadius: 24 }}>
                  <div className="flex items-center gap-2 mb-3">
                    <Microscope className="w-4 h-4" style={{ color: "var(--accent)" }} />
                    <p className="text-xs font-semibold tracking-widest uppercase" style={{ color: "var(--text-secondary)" }}>
                      Aetiology &amp; Cause
                    </p>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(240,244,255,0.7)" }}>{result?.cause}</p>
                </div>

                <motion.div
                  initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.4 }}
                  className="p-6 mb-5 md:mb-0"
                  style={{
                    borderRadius: 24,
                    background: "linear-gradient(135deg, rgba(99,202,255,0.10) 0%, rgba(168,85,247,0.10) 100%)",
                    border: "1px solid rgba(99,202,255,0.2)"
                  }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Stethoscope className="w-4 h-4" style={{ color: "var(--accent)" }} />
                    <p className="text-xs font-semibold tracking-widest uppercase" style={{ color: "var(--accent)" }}>
                      Recommended Protocol
                    </p>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>{result?.cure}</p>
                </motion.div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center" style={{ borderTop: "1px solid var(--border)" }}>
        <p className="text-xs font-medium tracking-wider" style={{ color: "rgba(240,244,255,0.2)" }}>
          DERMACARE VISION · NEURAL DIAGNOSTICS
        </p>
      </footer>
    </div>
  );
}
