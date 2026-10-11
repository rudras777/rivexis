// Original conceptual geometry. This renderer never reads wallets, RPCs or financial results.
export type AtlasRenderer={chapter:(value:number,environmental?:boolean)=>void;pointer:(x:number,y:number)=>void;active:(value:boolean)=>void;motion:(value:boolean)=>void;destroy:()=>void};
const vertex=`
attribute vec3 a_position;attribute vec3 a_normal;attribute vec3 a_color;
uniform float u_aspect,u_time,u_chapter,u_stage,u_dpr;uniform vec2 u_pointer;
varying vec3 v_color;varying float v_light,v_depth;
void main(){
 vec3 p=a_position;
 float boundary=smoothstep(1.0,2.0,u_chapter);
 p.y+=0.10*boundary*sin(p.x*1.8)+0.018*sin(u_time*0.32+p.x+p.z);
 float yaw=-0.30+u_pointer.x*0.045+0.06*sin(u_chapter*0.7);
 float pitch=0.58+u_pointer.y*0.025;
 mat3 ry=mat3(cos(yaw),0.0,-sin(yaw),0.0,1.0,0.0,sin(yaw),0.0,cos(yaw));
 mat3 rx=mat3(1.0,0.0,0.0,0.0,cos(pitch),sin(pitch),0.0,-sin(pitch),cos(pitch));
 vec3 normal=normalize(rx*ry*a_normal);p=rx*ry*p*mix(0.72,1.0,u_stage);
 float later=u_stage;
 p.x+=later*1.5;p.y-=mix(1.60,0.15,later);p.z-=mix(6.4,8.0,later);
 float near=0.1,far=20.0;
 gl_Position=vec4(p.x*2.65/u_aspect,p.y*2.65,-p.z*(far+near)/(far-near)-2.0*far*near/(far-near),-p.z);
 gl_PointSize=3.0*u_dpr;
 v_color=a_color;v_light=0.58+0.42*max(dot(normal,normalize(vec3(-0.4,0.9,0.7))),0.0);v_depth=clamp((-p.z-4.0)/10.0,0.0,1.0);
}`;
const fragment=`precision mediump float;varying vec3 v_color;varying float v_light,v_depth;uniform float u_alpha,u_kind,u_time,u_chapter;
void main(){float lighting=mix(v_light,1.0,step(0.5,u_kind));float alpha=u_alpha*(1.0-v_depth*0.35);
 if(u_kind>2.5){vec2 point=gl_PointCoord-0.5;if(length(point)>0.5)discard;}
 gl_FragColor=vec4(v_color*lighting,alpha);}`;
type Geometry={buffer:WebGLBuffer;count:number;mode:number;kind:number;alpha:number};
const teal=[128/255,170/255,161/255],bronze=[181/255,163/255,131/255],graphite=[34/255,48/255,52/255];
const height=(x:number,z:number)=>.20*Math.sin(x*1.3)+.30*Math.cos(z*1.4)+.10*x*z;
function vertexAt(x:number,z:number,layer:number,color:number[]){const dx=.26*Math.cos(x*1.3)+.10*z,dz=-.42*Math.sin(z*1.4)+.10*x;return [x,height(x,z)+layer,z,-dx,1,-dz,...color]}
export function createRiskAtlas(canvas:HTMLCanvasElement,onReady?:()=>void):AtlasRenderer|null{
 const context=canvas.getContext('webgl',{alpha:true,antialias:true,depth:true,powerPreference:'low-power',preserveDrawingBuffer:false});if(!context)return null;const gl:WebGLRenderingContext=context;
 const shaders:WebGLShader[]=[],buffers:WebGLBuffer[]=[];let program:WebGLProgram|null=null,disposed=false,frame=0,visible=true,moving=true,last=0,elapsed=0,chapter=0,targetChapter=0,stage=0,targetStage=0,px=0,py=0,targetX=0,targetY=0;
 let slowFrames=0,economy=false;
 const cleanup=()=>{cancelAnimationFrame(frame);for(const buffer of buffers)gl.deleteBuffer(buffer);for(const shader of shaders)gl.deleteShader(shader);if(program)gl.deleteProgram(program)};
 try{
  for(const [kind,source] of [[gl.VERTEX_SHADER,vertex],[gl.FRAGMENT_SHADER,fragment]] as const){const shader=gl.createShader(kind);if(!shader)throw Error('shader unavailable');shaders.push(shader);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('shader compile failed')}
  program=gl.createProgram();if(!program)throw Error('program unavailable');for(const shader of shaders)gl.attachShader(program,shader);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('shader link failed');gl.useProgram(program);
  const geometry=(data:number[],mode:number,kind:number,alpha:number):Geometry=>{const buffer=gl.createBuffer();if(!buffer)throw Error('buffer unavailable');buffers.push(buffer);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STATIC_DRAW);return {buffer,count:data.length/9,mode,kind,alpha}};
  const surface:number[]=[],contours:number[]=[],boundary:number[]=[],paths:number[]=[],nodes:number[]=[];
  const layers=[-.46,0,.46],nx=32,nz=20;
  for(const layer of layers){
   for(let ix=0;ix<nx;ix++)for(let iz=0;iz<nz;iz++){const x=-2.2+ix*4.4/nx,z=-1.1+iz*2.2/nz,xx=x+4.4/nx,zz=z+2.2/nz;for(const [a,b] of [[x,z],[xx,z],[x,zz],[x,zz],[xx,z],[xx,zz]])surface.push(...vertexAt(a,b,layer,graphite))}
   for(let row=0;row<=nz;row++)for(let col=0;col<nx;col++){const z=-1.1+row*2.2/nz,x=-2.2+col*4.4/nx;contours.push(...vertexAt(x,z,layer+.006,teal),...vertexAt(x+4.4/nx,z,layer+.006,teal))}
   for(let col=0;col<=nx;col+=4)for(let row=0;row<nz;row++){const x=-2.2+col*4.4/nx,z=-1.1+row*2.2/nz;contours.push(...vertexAt(x,z,layer+.008,teal),...vertexAt(x,z+2.2/nz,layer+.008,teal))}
  }
  for(let i=0;i<80;i++){const x=-2.2+i*4.4/80,xx=x+4.4/80;boundary.push(...vertexAt(x,.22*Math.sin(x*1.3),.48,bronze),...vertexAt(xx,.22*Math.sin(xx*1.3),.48,bronze))}
  for(let branch=-1;branch<=1;branch++)for(let i=0;i<48;i++){const x=-2+i*4/48,xx=x+4/48,z=branch*(.15+(x+2)*.17),zz=branch*(.15+(xx+2)*.17);paths.push(...vertexAt(x,z,.51,branch===0?bronze:teal),...vertexAt(xx,zz,.51,branch===0?bronze:teal))}
  for(const [x,z] of [[-1.9,-.7],[-1.1,.6],[-.2,-.4],[.9,.55],[1.8,-.7],[1.6,.75],[-1.6,.8]])nodes.push(...vertexAt(x,z,.49,bronze));
  const objects=[geometry(surface,gl.TRIANGLES,0,.72),geometry(contours,gl.LINES,1,.46),geometry(boundary,gl.LINES,2,.9),geometry(paths,gl.LINES,2,.9),geometry(nodes,gl.POINTS,3,.9)];
  const position=gl.getAttribLocation(program,'a_position'),normal=gl.getAttribLocation(program,'a_normal'),color=gl.getAttribLocation(program,'a_color');
  const uniforms=Object.fromEntries(['aspect','time','chapter','stage','dpr','pointer','alpha','kind'].map(name=>[name,gl.getUniformLocation(program!,`u_${name}`)]));
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.clearColor(0,0,0,0);
  function draw(now:number){
   if(disposed||!visible||gl.isContextLost())return;frame=0;
   const dt=Math.min(100,now-last||42);if(moving&&now-last<1000/(economy?12:24)){frame=requestAnimationFrame(draw);return}last=now;if(moving)elapsed+=dt/1000;const started=performance.now();
   chapter+=moving?(targetChapter-chapter)*.09:targetChapter-chapter;stage+=moving?(targetStage-stage)*.09:targetStage-stage;px+=moving?(targetX-px)*.12:targetX-px;py+=moving?(targetY-py)*.12:targetY-py;
   const dpr=Math.min(devicePixelRatio||1,economy?.75:1.5),w=Math.min(2304,Math.round(canvas.clientWidth*dpr)),h=Math.min(1440,Math.round(canvas.clientHeight*dpr));if(!w||!h)return;
   if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(program);
   gl.uniform1f(uniforms.aspect,w/h);gl.uniform1f(uniforms.time,elapsed);gl.uniform1f(uniforms.chapter,chapter);gl.uniform1f(uniforms.stage,stage);gl.uniform1f(uniforms.dpr,dpr);gl.uniform2f(uniforms.pointer,px,py);
   for(let i=0;i<objects.length;i++){const object=objects[i];gl.bindBuffer(gl.ARRAY_BUFFER,object.buffer);for(const [location,offset] of [[position,0],[normal,12],[color,24]]){gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,3,gl.FLOAT,false,36,offset)}
    const environment=1-stage*.74;const emphasis=i===3?Math.max(0,1-Math.abs(chapter-4)):1;
    gl.uniform1f(uniforms.alpha,object.alpha*environment*emphasis);gl.uniform1f(uniforms.kind,object.kind);gl.depthMask(i===0);gl.drawArrays(object.mode,0,object.count);
   }gl.depthMask(true);slowFrames=performance.now()-started>40||dt>85?slowFrames+1:0;if(slowFrames>=8)economy=true;canvas.dataset.quality=economy?'economy':'balanced';if(canvas.dataset.renderer!=='webgl'){canvas.dataset.renderer='webgl';onReady?.()}canvas.dataset.motion=moving?'running':'paused';if(moving)frame=requestAnimationFrame(draw);
  }
  const request=()=>{if(!disposed&&visible&&!frame)frame=requestAnimationFrame(draw)};
  const resize=new ResizeObserver(request);resize.observe(canvas);request();
  return {chapter:(value,environmental=false)=>{targetChapter=Math.max(0,Math.min(5,value));targetStage=environmental?1:0;request()},pointer:(x,y)=>{targetX=Math.max(-1,Math.min(1,x));targetY=Math.max(-1,Math.min(1,y));request()},active:value=>{visible=value;canvas.dataset.visible=String(value);cancelAnimationFrame(frame);frame=0;canvas.dataset.motion=value&&moving?'running':'paused';if(value)request()},motion:value=>{moving=value;targetX=0;targetY=0;cancelAnimationFrame(frame);frame=0;request()},destroy:()=>{disposed=true;resize.disconnect();cleanup();delete canvas.dataset.renderer;canvas.dataset.motion='disposed'}};
 }catch{cleanup();return null}
}
