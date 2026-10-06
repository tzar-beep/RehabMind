"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

interface FlickeringGridProps {
  squareSize?: number;
  gridGap?: number;
  /** Chance per second that a square changes brightness. */
  flickerChance?: number;
  /** Any CSS colour. */
  color?: string;
  maxOpacity?: number;
  className?: string;
}

/**
 * FlickeringGrid — a canvas of small squares that gently change brightness. Decorative.
 * Fills its parent. Pauses when off-screen; draws one still frame with reduced motion.
 */
export function FlickeringGrid({
  squareSize = 4,
  gridGap = 6,
  flickerChance = 0.3,
  color = "rgb(0, 0, 0)",
  maxOpacity = 0.3,
  className,
}: FlickeringGridProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    // Resolve the colour to "rgba(r, g, b," once.
    const probe = document.createElement("canvas").getContext("2d");
    let rgba = "rgba(0, 0, 0,";
    if (probe) {
      probe.fillStyle = color;
      probe.fillRect(0, 0, 1, 1);
      const [r, g, b] = probe.getImageData(0, 0, 1, 1).data;
      rgba = `rgba(${r}, ${g}, ${b},`;
    }

    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const step = squareSize + gridGap;
    let cols = 0;
    let rows = 0;
    let dpr = 1;
    let squares = new Float32Array(0);
    let frame = 0;
    let last = 0;
    let visible = true;

    const setup = () => {
      dpr = window.devicePixelRatio || 1;
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
      cols = Math.ceil(canvas.clientWidth / step);
      rows = Math.ceil(canvas.clientHeight / step);
      squares = Float32Array.from(
        { length: cols * rows },
        () => Math.random() * maxOpacity,
      );
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          ctx.fillStyle = `${rgba}${squares[i * rows + j]})`;
          ctx.fillRect(
            i * step * dpr,
            j * step * dpr,
            squareSize * dpr,
            squareSize * dpr,
          );
        }
      }
    };

    const tick = (time: number) => {
      const dt = last ? (time - last) / 1000 : 0;
      last = time;
      for (let i = 0; i < squares.length; i++) {
        if (Math.random() < flickerChance * dt)
          squares[i] = Math.random() * maxOpacity;
      }
      draw();
      if (visible) frame = requestAnimationFrame(tick);
    };

    setup();
    draw();
    if (!still) frame = requestAnimationFrame(tick);

    const resize = new ResizeObserver(() => {
      setup();
      draw();
    });
    resize.observe(canvas);
    const view = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      cancelAnimationFrame(frame);
      last = 0;
      if (visible && !still) frame = requestAnimationFrame(tick);
    });
    view.observe(canvas);

    return () => {
      cancelAnimationFrame(frame);
      resize.disconnect();
      view.disconnect();
    };
  }, [squareSize, gridGap, flickerChance, color, maxOpacity]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={cn("pointer-events-none block size-full", className)}
    />
  );
}
