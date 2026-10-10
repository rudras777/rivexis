# Visual implementation research and decision

The page uses a financial risk-field illustration rather than a generic floating object. The serif editorial headline, breathing room, hairline constraints and continuous dark canvas preserve RIVEXIS's approved royal palette and vector brand identity. Existing brand SVG paths remain the crisp master at every size.

| Option | Assessment | Decision |
| --- | --- | --- |
| Native SVG + CSS 3D | Vector contours, preserve-3D depth, no texture request or extra runtime; event-only tilt with static fallback | Implemented |
| Three.js / React Three Fiber | Useful for complex interactive scenes; requires renderer/resource management and performance budgeting | Rejected for this small risk illustration |
| GSAP / ScrollTrigger | Powerful sequencing; additional code and scroll choreography unnecessary for restrained editorial sections | Native transitions and scrolling |
| Motion | Strong reduced-motion APIs; no existing need for a new animation dependency | Media-query/accessibility equivalent |
| Lenis | Smooth scrolling toolkit; interception changes browser behavior and adds a runtime | Native smooth scrolling only where motion is permitted |
| Rive | Authored state machines and WASM runtime suited to richer animations | Not needed |
| Spline | Hosted scenes and runtime add dependency and scene transfer overhead | Not needed |

Primary technical references consulted:
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform-style
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion
- https://r3f.docs.pmnd.rs/advanced/scaling-performance
- https://threejs.org/manual/
- https://gsap.com/docs/v3/Plugins/ScrollTrigger/
- https://motion.dev/docs/react-accessibility
- https://lenis.dev/
- https://rive.app/docs/runtimes/web/web-js
- https://spline.design/

Visual references consulted: Awwwards 3D mouse parallax (https://www.awwwards.com/inspiration/3d-parallax-with-mouse-movement-soul-aether) and Finely Crafted (https://www.awwwards.com/sites/finely-crafted). These inform restrained depth/editorial rhythm, not copied assets or a claim of reviewing every project. An Immersive Garden fetch was unsuccessful.

Implementation limits: maximum small pointer rotation; requestAnimationFrame only coalesces real pointer events; no idle loop; unregister listeners/cancel RAF on unmount, media change, pointer leave. Touch, coarse pointer, forced colors and reduced motion retain static art/native cursor. The optional hover bracket never hides the system cursor and does not enter financial workspace controls. Mobile geometry fits within actual layout instead of masking overflow. Public art is explicitly conceptual, not live financial data.
