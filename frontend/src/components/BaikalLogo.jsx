/**
 * BaikalLogo - SVG 인라인 로고 컴포넌트
 * PNG 이미지 파일의 '.AI' 클리핑 문제 없이 항상 선명하게 렌더링
 */
export default function BaikalLogo({ className = '' }) {
  return (
    <svg
      viewBox="0 0 360 92"
      style={{ aspectRatio: '360 / 92' }}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      aria-label="BAIKAL.AI"
    >
      <text
        x="4"
        y="60"
        fontFamily="'Inter', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
        fontWeight="900"
        fontSize="56"
        letterSpacing="-1"
      >
        <tspan fill="white">BAIKAL</tspan>
        <tspan fill="#DC2626">.AI</tspan>
      </text>
      <line x1="4" y1="70" x2="356" y2="70" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
      <circle cx="16" cy="83" r="9" fill="#4B5BCC" />
      <circle cx="42" cy="83" r="9" fill="#6BD9A0" />
      <circle cx="68" cy="83" r="9" fill="#E84A30" />
      <circle cx="94" cy="83" r="9" fill="#F5C030" />
    </svg>
  );
}
