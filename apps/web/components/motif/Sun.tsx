import type { SVGProps } from "react";

/**
 * One ray pointing up: a triangle from the top of the box to a 4-unit base
 * whose corners sit on the disc's edge (5.75 from the center). The other seven
 * are this one rotated about the center. Bold enough to fill the 24px icon
 * box like a stroked lucide icon, and to read as a sun in a 16px favicon.
 */
const RAY = "M12 .75 14 6.61 10 6.61z";
const ANGLES = [0, 45, 90, 135, 180, 225, 270, 315];

/**
 * The eight-ray sun of the Philippine flag (plan 012, D39), the app's one
 * motif. Drawn in currentColor on a 24px grid like a lucide icon, so it
 * swaps in for one without moving anything. Decorative: aria-hidden, and
 * data-motif so the layout gate (e2e/layout.spec.ts) leaves it out. No ids,
 * so any number of suns can share a page.
 */
export function Sun(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      data-motif=""
      {...props}
    >
      <circle cx="12" cy="12" r="5.75" />
      {ANGLES.map((a) => (
        <path key={a} d={RAY} transform={`rotate(${a} 12 12)`} />
      ))}
    </svg>
  );
}
