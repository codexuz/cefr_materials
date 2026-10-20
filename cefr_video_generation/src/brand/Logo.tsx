import React from "react";

export const BRAND_BLUE = "#0356FE";

// Impulse Learning Center mark, redrawn as vector (256×256 grid, traced from the PNG logo)
// so it stays sharp at any size and each stroke can be drawn on.
// All progress values are 0..1.
export const Logo: React.FC<{
  size: number;
  circle?: number;
  book?: number;
  spine?: number;
  flame?: number;
}> = ({ size, circle = 1, book = 1, spine = 1, flame = 1 }) => {
  // pathLength=1 lets dashoffset = 1 - progress draw each path regardless of its real length.
  const draw = (p: number) => ({ strokeDasharray: 1, strokeDashoffset: 1 - p });
  return (
    <svg width={size} height={size} viewBox="0 0 256 256" style={{ overflow: "visible" }}>
      <circle cx={128} cy={128} r={128 * circle} fill={BRAND_BLUE} />
      <g fill="none" stroke="#FFFFFF" strokeLinejoin="miter" strokeMiterlimit={10}>
        {book < 1 ? (
          <>
            {/* Pages: each drawn from the spine outward and around to the bottom tip */}
            <path d="M129 116 Q 112 98.7 73.7 98.7 L 73.7 173.7 Q 110 173.7 129 199.3" strokeWidth={10.7} pathLength={1} {...draw(book)} />
            <path d="M129 116 Q 146 98.7 184.3 98.7 L 184.3 173.7 Q 148 173.7 129 199.3" strokeWidth={10.7} pathLength={1} {...draw(book)} />
          </>
        ) : (
          // Finished: one closed outline so the bottom tip and spine top get clean mitred joins.
          <path
            d="M129 116 Q 112 98.7 73.7 98.7 L 73.7 173.7 Q 110 173.7 129 199.3 Q 148 173.7 184.3 173.7 L 184.3 98.7 Q 146 98.7 129 116 Z"
            strokeWidth={10.7}
          />
        )}
        {/* Flame: almond outline above the spine */}
        <path
          d="M129 54 C 146 67, 146 94, 129 107.5 C 112 94, 112 67, 129 54 Z"
          strokeWidth={8}
          {...(flame < 1 ? { pathLength: 1, ...draw(flame) } : {})}
        />
      </g>
      {/* Spine with bookmark notch, wiped down from the top */}
      <polygon
        points="124 112 134 112 134 155 129 150 124 155"
        fill="#FFFFFF"
        style={{ clipPath: `inset(0 0 ${(1 - spine) * 100}% 0)` }}
      />
    </svg>
  );
};
