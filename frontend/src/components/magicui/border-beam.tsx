"use client";

import { motion, type MotionStyle } from "motion/react";
import { useSyncExternalStore } from "react";

import { cn } from "@/lib/utils";

interface BorderBeamProps {
  /** Length of the beam in px. */
  size?: number;
  /** Seconds for one lap of the border. */
  duration?: number;
  /** Start this many seconds into the lap. */
  delay?: number;
  colorFrom?: string;
  colorTo?: string;
  className?: string;
  reverse?: boolean;
  /** Border width of the beam in px. */
  borderWidth?: number;
}

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(onChange: () => void) {
  const media = window.matchMedia(QUERY);
  media.addEventListener("change", onChange);
  return () => media.removeEventListener("change", onChange);
}

const prefersMotion = () => !window.matchMedia(QUERY).matches;

/**
 * A beam of light that travels along its container's border. Decorative only; not
 * rendered at all with prefers-reduced-motion. The container needs `relative`.
 */
export function BorderBeam({
  className,
  size = 50,
  delay = 0,
  duration = 6,
  colorFrom = "#ffaa40",
  colorTo = "#9c40ff",
  reverse = false,
  borderWidth = 1,
}: BorderBeamProps) {
  const animate = useSyncExternalStore(subscribe, prefersMotion, () => false);
  if (!animate) return null;

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 rounded-[inherit] border-(length:--border-beam-width) border-transparent mask-[linear-gradient(transparent,transparent),linear-gradient(#000,#000)] mask-intersect [mask-clip:padding-box,border-box]"
      style={
        { "--border-beam-width": `${borderWidth}px` } as React.CSSProperties
      }
    >
      <motion.div
        className={cn(
          "absolute aspect-square",
          "bg-linear-to-l from-(--color-from) via-(--color-to) to-transparent",
          className,
        )}
        style={
          {
            width: size,
            offsetPath: `rect(0 auto auto 0 round ${size}px)`,
            "--color-from": colorFrom,
            "--color-to": colorTo,
          } as MotionStyle
        }
        initial={{ offsetDistance: "0%" }}
        animate={{
          offsetDistance: reverse ? ["100%", "0%"] : ["0%", "100%"],
        }}
        transition={{
          repeat: Infinity,
          ease: "linear",
          duration,
          delay: -delay,
        }}
      />
    </div>
  );
}
