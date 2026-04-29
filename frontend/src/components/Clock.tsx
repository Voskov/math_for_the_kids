interface ClockProps {
  hour: number;
  minute: number;
  size?: number;
}

export default function Clock({ hour, minute, size = 200 }: ClockProps) {
  const minAngle = minute * 6;
  const hrAngle = (hour % 12) * 30 + minute * 0.5;
  const numbers = [];
  for (let i = 1; i <= 12; i++) {
    const a = (i * 30 * Math.PI) / 180;
    numbers.push(
      <text
        key={i}
        x={Math.sin(a) * 38}
        y={-Math.cos(a) * 38 + 4}
        textAnchor="middle"
        fontSize="11"
        fontWeight="600"
        fill="#222"
      >
        {i}
      </text>
    );
  }
  const ticks = [];
  for (let i = 0; i < 60; i++) {
    const a = i * 6;
    const long = i % 5 === 0;
    ticks.push(
      <line
        key={i}
        x1="0"
        y1={long ? -46 : -47}
        x2="0"
        y2={long ? -49 : -49}
        stroke="#333"
        strokeWidth={long ? 1.5 : 0.5}
        transform={`rotate(${a})`}
      />
    );
  }
  return (
    <svg viewBox="-50 -50 100 100" width={size} height={size} style={{ display: "block" }}>
      <circle r="49" fill="#fff" stroke="#222" strokeWidth="2" />
      {ticks}
      {numbers}
      <line
        x1="0"
        y1="4"
        x2="0"
        y2="-26"
        stroke="#222"
        strokeWidth="3.5"
        strokeLinecap="round"
        transform={`rotate(${hrAngle})`}
      />
      <line
        x1="0"
        y1="6"
        x2="0"
        y2="-40"
        stroke="#444"
        strokeWidth="2"
        strokeLinecap="round"
        transform={`rotate(${minAngle})`}
      />
      <circle r="2.5" fill="#222" />
    </svg>
  );
}

export function parseTime(s: string): { hour: number; minute: number } {
  const [h, m] = s.split(":").map((x) => parseInt(x, 10));
  return { hour: h, minute: m || 0 };
}
