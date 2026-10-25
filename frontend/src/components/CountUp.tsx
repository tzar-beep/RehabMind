"use client";

import { NumberTicker } from "@/components/magicui/number-ticker";

/**
 * A number that counts up once when it comes into view (Magic UI Number Ticker). Screen
 * readers get the final value at once; the counting digits are hidden from them.
 */
export function CountUp({ value }: { value: number }) {
  return (
    <>
      <span aria-hidden="true">
        <NumberTicker value={value} />
      </span>
      <span className="sr-only">{value}</span>
    </>
  );
}
