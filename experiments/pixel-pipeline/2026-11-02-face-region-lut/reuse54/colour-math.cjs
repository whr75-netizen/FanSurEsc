'use strict';
// Pure numeric subset reused from31/ramp-core.js (RGB/OKLab and fixed-L/h
// chroma reduction). No default colour, material-role table or HairAnchor.
const decode=x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4;
const encode=x=>x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;
function labLinear([r,g,b]){const l=Math.cbrt(.4122214708*r+.5363325363*g+.0514459929*b),m=Math.cbrt(.2119034982*r+.6806995451*g+.1073969566*b),s=Math.cbrt(.0883024619*r+.2817188376*g+.6299787005*b);return [.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s];}
function rgbLab(rgb){return labLinear(rgb.map(v=>decode(v/255)));}
function lch(rgb){const [L,a,b]=rgbLab(rgb);return {L,C:Math.hypot(a,b),h:Math.atan2(b,a)};}
function linearLch(L,C,h){const a=C*Math.cos(h),b=C*Math.sin(h),l=(L+.3963377774*a+.2158037573*b)**3,m=(L-.1055613458*a-.0638541728*b)**3,s=(L-.0894841775*a-1.291485548*b)**3;return [4.0767416621*l-3.3077115913*m+.2309699292*s,-1.2684380046*l+2.6097574011*m-.3413193965*s,-.0041960863*l-.7034186147*m+1.707614701*s];}
function gamut(L,C,h){
 const valid=v=>v.every(x=>x>=-1e-9&&x<=1+1e-9);let usedC=C,v=linearLch(L,C,h);
 if(!valid(v)){let lo=0,hi=C;for(let i=0;i<28;i++){const mid=(lo+hi)/2;if(valid(linearLch(L,mid,h)))lo=mid;else hi=mid;}usedC=lo;v=linearLch(L,usedC,h);}
 return {rgb8:v.map(x=>Math.round(255*encode(Math.max(0,Math.min(1,x))))),usedC,gamutReduced:C-usedC>1e-7};
}
module.exports={decode,encode,labLinear,rgbLab,lch,linearLch,gamut};
