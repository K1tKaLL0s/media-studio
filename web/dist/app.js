export const STRINGS = {
  zh: {
    brand:'媒体工作台',brandNote:'把想法变成声音与画面',language:'界面语言',tools:'创作工具',create:'开始创作',localNote:'素材与生成任务由你指定的本机工作台处理。',advanced:'打开高级图表',connectionSettings:'连接设置',close:'关闭',gatewayAddress:'工作台地址',gatewayHelp:'本机使用下方回环地址。远端工作台请填你信任的 HTTPS 地址；本页不会扫描网络。',networkPermissionHelp:'首次从网站连接本机时，浏览器可能请求“本地网络访问”权限。请按浏览器正常提示授权，并确认本机网关已经启动。',useLocalGateway:'使用本机地址',saveAndConnect:'保存并连接',resources:'工作台资源',refresh:'刷新',freeMemory:'请求释放',result:'本次结果',technicalDetails:'技术详情',privacyNote:'本页不提供云端推理。上传的素材将发送到上方连接设置指定的工作台。',loadExample:'填入示例文字',run:'开始生成',retry:'安全重试同一请求',submitting:'正在提交…',runHelp:'任务串行执行，生成期间请保持工作台在线。',formHint:'切换界面语言会保留你已编辑的内容。',catalogLoading:'正在读取工作台的真实配置…',catalogMissing:'尚未连接工作台，连接成功后可填写参数。',offline:'工作台未连接',backendOffline:'生成服务离线',connected:'工作台已连接',busy:'工作台处理中',connecting:'正在连接',available:'可用内存',headroom:'提交余量',commit:'系统提交量',gpu:'可用显存',unavailable:'不可测',queue:'任务队列',queueValue:'运行 {running} · 等待 {pending}',resourceNote:'资源来自本机实测；提交余量与物理可用内存分别统计。',idleArmed:'空闲 {seconds} 秒后请求释放',idleReady:'空闲释放已启用',lastFreed:'已请求空闲释放',resourcesOffline:'连接后显示真实内存与队列状态。',experimental:'实验',videoWarning:'视频内容尚未通过验收。当前输出可能出现画面异常，请作为实验功能使用。',emptyTitle:'让创作从这里开始',emptyBody:'选择工具、填写内容，生成结果会显示在这里。',workingTitle:'任务正在处理',workingBody:'模型加载与生成可能需要几分钟。这里显示真实任务状态，不提供估算进度。',pendingTitle:'任务已排队',pendingBody:'正在等待生成服务开始处理。',unknownTitle:'提交结果待确认',unknownBody:'连接中断时请重试同一请求，工作台会按请求编号去重。',errorTitle:'本次任务未完成',cancelledTitle:'任务已取消',cancelledBody:'取消状态已由工作台确认。',cancelRequested:'取消已请求，正在等待任务状态确认。',cancel:'取消本次任务',cancelling:'正在请求取消…',download:'下载原文件',mediaLoading:'正在读取结果媒体…',mediaUnavailable:'媒体暂时无法读取，请刷新重试。',retryMedia:'重试预览',outputNumber:'结果 {number}',jobReference:'任务编号',chooseImage:'选择图片',chooseAudio:'选择参考音频',imageTypes:'PNG、JPEG 或 WebP，最大 32 MiB',audioTypes:'WAV 或 FLAC，最大 32 MiB',chooseSample:'或选用本机示例素材',noSample:'没有可用示例',clearAsset:'移除',uploading:'正在上传…',required:'请填写此项。',numberInvalid:'请输入范围内的有效数字。',integerInvalid:'此项需要整数。',optionInvalid:'请选择有效选项。',assetRequired:'请选择或上传有效素材。',fieldRange:'{min}–{max}',optional:'选填',releaseRequested:'释放已请求，资源已稳定。',releasedUnknown:'释放已请求；原生服务没有提供消费确认。',runBlocked:'请等待当前任务结束后再生成。',cancelReason:'工作台已按资源保护条件取消本次任务。',localPreview:'此预览来自本次真实输出。',taskSuccess:'已完成',taskError:'未完成',taskCancelled:'已取消',taskPending:'等待中',taskRunning:'生成中',taskUnknown:'待确认',taskEmpty:'待创作',newConnection:'已保存连接地址。',noOutput:'任务没有返回可展示的媒体。',imageLabel:'图片',audioLabel:'音频',videoLabel:'视频',samplePrefix:'本机示例',unknownStatus:'状态暂时不可用',renderFailure:'媒体无法在浏览器中解码，可下载原文件检查。'
  },
  en: {
    brand:'Media Studio',brandNote:'Turn ideas into sound and images',language:'Interface language',tools:'CREATIVE TOOLS',create:'CREATE SOMETHING',localNote:'Your chosen local studio handles the source files and generation tasks.',advanced:'Open advanced graph',connectionSettings:'Connection settings',close:'Close',gatewayAddress:'Studio address',gatewayHelp:'Use the loopback address below for this computer. For a remote studio, enter an HTTPS address you trust. This page never scans the network.',networkPermissionHelp:'When this website first connects to your computer, your browser may request Local Network Access. Use the normal browser prompt and make sure the local gateway is running.',useLocalGateway:'Use local address',saveAndConnect:'Save and connect',resources:'Studio resources',refresh:'Refresh',freeMemory:'Request release',result:'Current result',technicalDetails:'Technical details',privacyNote:'This page does not provide cloud inference. Uploaded files go to the studio address selected in connection settings.',loadExample:'Use example text',run:'Start creating',retry:'Safely retry the same request',submitting:'Submitting…',runHelp:'Tasks run one at a time. Keep the studio online during generation.',formHint:'Changing the interface language preserves text you have edited.',catalogLoading:'Reading the actual studio configuration…',catalogMissing:'Connect to the studio to load the available controls.',offline:'Studio disconnected',backendOffline:'Generation service offline',connected:'Studio connected',busy:'Studio is working',connecting:'Connecting',available:'Available memory',headroom:'Commit headroom',commit:'System commit',gpu:'Free VRAM',unavailable:'Unavailable',queue:'Task queue',queueValue:'Running {running} · Pending {pending}',resourceNote:'Measured on your computer. Commit headroom and available physical memory are separate values.',idleArmed:'Release requested after {seconds}s idle',idleReady:'Idle release enabled',lastFreed:'Idle release requested',resourcesOffline:'Connect to see actual memory and queue status.',experimental:'Experimental',videoWarning:'Video content has not passed acceptance review. Outputs may contain visual defects. Treat this tool as experimental.',emptyTitle:'Your next creation starts here',emptyBody:'Choose a tool and add your content. The generated result will appear here.',workingTitle:'Your task is being processed',workingBody:'Loading a model and generating can take several minutes. This shows actual task status without an estimated progress bar.',pendingTitle:'Your task is queued',pendingBody:'Waiting for the generation service to start processing.',unknownTitle:'Submission needs confirmation',unknownBody:'If the connection was interrupted, retry the same request. The studio uses its request ID to prevent duplicate submissions.',errorTitle:'This task did not complete',cancelledTitle:'Task cancelled',cancelledBody:'The studio has confirmed the cancelled status.',cancelRequested:'Cancellation requested. Waiting for the studio to confirm the task status.',cancel:'Cancel this task',cancelling:'Requesting cancellation…',download:'Download original',mediaLoading:'Loading result media…',mediaUnavailable:'The media could not be loaded. Refresh to try again.',retryMedia:'Retry preview',outputNumber:'Result {number}',jobReference:'Task ID',chooseImage:'Choose an image',chooseAudio:'Choose reference audio',imageTypes:'PNG, JPEG or WebP, up to 32 MiB',audioTypes:'WAV or FLAC, up to 32 MiB',chooseSample:'Or choose a local sample',noSample:'No samples available',clearAsset:'Remove',uploading:'Uploading…',required:'Please fill in this field.',numberInvalid:'Enter a valid number within the allowed range.',integerInvalid:'Enter a whole number.',optionInvalid:'Choose a valid option.',assetRequired:'Choose or upload a valid source file.',fieldRange:'{min}–{max}',optional:'Optional',releaseRequested:'Release requested; resources stable.',releasedUnknown:'Release requested; the native service does not acknowledge consumption.',runBlocked:'Wait for the current task to finish before starting another.',cancelReason:'The studio cancelled this task under its resource protection rules.',localPreview:'This preview comes from the actual task output.',taskSuccess:'Complete',taskError:'Incomplete',taskCancelled:'Cancelled',taskPending:'Pending',taskRunning:'Generating',taskUnknown:'Unconfirmed',taskEmpty:'Ready to create',newConnection:'Connection address saved.',noOutput:'The task returned no media to display.',imageLabel:'Image',audioLabel:'Audio',videoLabel:'Video',samplePrefix:'Local sample',unknownStatus:'Status is temporarily unavailable',renderFailure:'The browser could not decode this media. Download the original to inspect it.'
  }
};

export const ERRORS = {
  zh:{BAD_JSON:'请求格式无效。',INVALID_REQUEST:'请求信息不完整。',UNKNOWN_PROFILE:'此创作工具不存在。',UNKNOWN_FIELD:'请求包含不支持的参数。',INVALID_VALUE:'参数值无效，请检查表单。',MISSING_ASSET:'素材不存在，请重新选择或上传。',INVALID_PROJECT:'请选择工作台中已有的项目。',BUSY:'工作台已有任务，请等待完成。',LOW_RESOURCES:'当前内存或提交余量不足，请释放资源后重试。',BACKEND_UNAVAILABLE:'本机生成服务不可用，请确认它已经启动。',VALIDATION_FAILED:'工作流验证未通过，请查看技术详情。',SUBMISSION_UNCERTAIN:'提交结果尚不明确，请安全重试同一请求。',UNKNOWN_JOB:'工作台找不到此任务记录。',NOT_RUNNING:'此任务当前没有运行。',FORBIDDEN_HOST:'此工作台地址未获网关允许。',FORBIDDEN_ORIGIN:'此网站尚未获本机网关允许，请检查网站来源配置。',UNSUPPORTED_MEDIA:'不支持此素材格式。',UPLOAD_TOO_LARGE:'素材超过 32 MiB 上限。',NOT_FOUND:'找不到所请求的文件。',INTERNAL_ERROR:'工作台出现内部错误，请查看技术详情。',EXECUTION_ERROR:'生成过程出现错误，请查看技术详情。',NO_OUTPUT:'任务没有返回可展示的媒体。',RELEASE_PENDING:'释放请求后的资源仍在变化，请稍后重试。',NETWORK_ERROR:'无法连接工作台。请确认地址、网关进程和浏览器本地网络权限。',INVALID_GATEWAY:'请输入 HTTP 回环地址或你信任的 HTTPS 根地址，不要包含账户信息、路径或查询参数。',INVALID_ASSET_URL:'结果媒体地址不属于当前工作台。',UPLOAD_TYPE:'请选择 PNG、JPEG、WebP 图片，或 WAV、FLAC 音频。',UNEXPECTED_RESPONSE:'工作台返回了无法识别的响应。'},
  en:{BAD_JSON:'The request format is invalid.',INVALID_REQUEST:'The request is incomplete.',UNKNOWN_PROFILE:'This creative tool does not exist.',UNKNOWN_FIELD:'The request contains an unsupported field.',INVALID_VALUE:'A parameter is invalid. Check the form.',MISSING_ASSET:'The source file is missing. Choose or upload it again.',INVALID_PROJECT:'Choose an existing studio project.',BUSY:'The studio already has a task. Wait for it to finish.',LOW_RESOURCES:'Available memory or commit headroom is too low. Release resources and try again.',BACKEND_UNAVAILABLE:'The local generation service is unavailable. Make sure it is running.',VALIDATION_FAILED:'Workflow validation failed. See technical details.',SUBMISSION_UNCERTAIN:'The submission result is uncertain. Safely retry the same request.',UNKNOWN_JOB:'The studio could not find this task record.',NOT_RUNNING:'This task is not currently running.',FORBIDDEN_HOST:'This studio address is not allowed by the gateway.',FORBIDDEN_ORIGIN:'This website is not allowed by the local gateway. Check the configured website origin.',UNSUPPORTED_MEDIA:'This media format is not supported.',UPLOAD_TOO_LARGE:'The file exceeds the 32 MiB limit.',NOT_FOUND:'The requested file could not be found.',INTERNAL_ERROR:'The studio encountered an internal error. See technical details.',EXECUTION_ERROR:'Generation encountered an error. See technical details.',NO_OUTPUT:'The task returned no media to display.',RELEASE_PENDING:'Resources are still changing after the release request. Try again shortly.',NETWORK_ERROR:'Cannot connect to the studio. Check the address, gateway process and browser Local Network Access permission.',INVALID_GATEWAY:'Enter an HTTP loopback address or an HTTPS root address you trust, without account information, a path or query parameters.',INVALID_ASSET_URL:'The result media URL does not belong to this studio.',UPLOAD_TYPE:'Choose a PNG, JPEG or WebP image, or WAV or FLAC audio file.',UNEXPECTED_RESPONSE:'The studio returned an unrecognized response.'}
};
ERRORS.zh.LOST_TASK='队列与历史中暂时找不到此任务；工作台不会自动重新提交。';
ERRORS.en.LOST_TASK='The task is absent from the queue and history. The studio will not resubmit it automatically.';
ERRORS.zh.BACKEND_RESTARTED='生成服务已重启，本次任务未完成，请检查后重新开始。';
ERRORS.en.BACKEND_RESTARTED='The generation service restarted before this task completed. Check the studio before starting again.';

export const PROFILES = [
  ['voice_design','音色设计','Voice design','用文字描述音色','Describe a voice','Qwen3-TTS VoiceDesign'],
  ['speech_index25','Index参考声音','Index reference voice','参考声音与时长控制','Reference & duration','IndexTTS 2.5'],
  ['music','音乐生成','Music generation','旋律、歌词与配乐','Music, lyrics & score','ACE-Step 1.5'],
  ['speech','语音合成','Speech synthesis','朗读与音色','Text & voice','Qwen3-TTS'],
  ['speech_clone','参考音色','Voice cloning','参考音频与文本','Reference & text','Qwen3-TTS'],
  ['anime','插画创作','Illustration','文字生成插画','Text to illustration','Anima'],
  ['image','图像创作','Image creation','文字生成图像','Text to image','FLUX.2 Klein'],
  ['image-edit','图像编辑','Image editing','按指令修改图片','Edit with instructions','FLUX.2 Klein'],
  ['video','短视频','Short video','文字生成视频','Text to video','Wan 2.2'],
  ['video-i2v','图片动起来','Animate an image','图片生成视频','Image to video','Wan 2.2'],
  ['mv','歌词影像','Lyric video','渲染已有项目','Render a project','PV / MV']
];

export const EXAMPLES = {
  voice_design:{text:{zh:'今天的故事，从一阵轻轻的风开始。',en:'Today’s story begins with a gentle breeze.'},instruct:{zh:'成年女声，温暖、清晰，语速舒缓，像在轻声讲故事。',en:'A warm adult female voice, clearly articulated, with a gentle storytelling pace.'}},
  speech_index25:{text:{zh:'今天的故事，从一阵轻轻的风开始。',en:'Today’s story begins with a gentle breeze.'}},
  music:{caption:{zh:'A quiet acoustic piano instrumental, gentle and unhurried, soft strings, suitable for a fable',en:'A quiet acoustic piano instrumental, gentle and unhurried, soft strings, suitable for a fable'},lyrics:{zh:'[Instrumental]',en:'[Instrumental]'}},
  speech:{text:{zh:'你好，欢迎来到媒体工作台。愿今天的创作，为你的想法带来新的声音。',en:'Hello, welcome to Media Studio. Let today’s creation bring a new voice to your ideas.'},instruct:{zh:'语气平静、清晰，像与朋友自然交谈。',en:'Speak calmly and clearly, as if talking with a friend.'}},
  speech_clone:{text:{zh:'这是一段使用参考音色生成的示例。请先上传你的参考音频，并填写准确的参考文本。',en:'This is an example using a reference voice. Upload your reference recording and enter its exact transcript first.'},language:{zh:'Chinese',en:'English'},reference_text:{zh:'',en:''}},
  anime:{prompt:{zh:'柔和的手绘动画插画，一位穿米白色外套的年轻女子站在海边小镇的街角，手中捧着一束小花，微风吹动头发，清晨的暖光，完整人物，安静而明亮的画面。',en:'A soft hand-drawn anime illustration of a young woman in a cream coat standing on a street corner in a seaside town, holding a small bouquet, hair moving in a gentle breeze, warm morning light, complete figure, a quiet and luminous scene.'},negative_prompt:{zh:'模糊，低质量，畸形，额外的手指，额外的四肢，文字，水印，签名',en:'blur, low quality, deformation, extra fingers, extra limbs, text, watermark, signature'}},
  image:{prompt:{zh:'一只青绿色陶瓷茶壶放在浅灰色桌面上，柔和的侧面窗光，极简静物摄影，真实陶瓷釉面，干净背景，清晰细节。',en:'A teal ceramic teapot on a light gray tabletop, soft window light from the side, minimal still life photography, realistic glazed ceramic, clean background, crisp details.'}},
  'image-edit':{prompt:{zh:'将茶壶改为柔和的珊瑚红色，保持茶壶形状、位置、背景、光线和阴影不变。',en:'Change the teapot to a soft coral red while preserving its shape, position, background, lighting and shadows.'}},
  video:{prompt:{zh:'一只白色纸船在宁静的池塘上缓缓漂动，水面泛起细小涟漪，柔和的自然光，镜头保持稳定，画面连贯。',en:'A white paper boat drifts slowly across a calm pond, creating small ripples in soft natural light. The camera stays still and the scene remains coherent.'},negative_prompt:{zh:'模糊，失真，闪烁，彩色条纹，文字，水印，突然的镜头切换',en:'blur, distortion, flicker, colored stripes, text, watermark, sudden cuts'}},
  'video-i2v':{prompt:{zh:'让画面中的主体产生轻微自然的运动，保持原图构图、颜色和光线，镜头稳定，动作平缓。',en:'Add subtle natural movement to the subject while preserving the composition, colors and lighting of the source image. Keep the camera still and the motion gentle.'},negative_prompt:{zh:'模糊，失真，闪烁，彩色条纹，文字，水印，突然的镜头切换',en:'blur, distortion, flicker, colored stripes, text, watermark, sudden cuts'}}
};

const FIELD_LABELS = {
  text:['朗读文本','Text to speak'],language:['朗读语言','Speech language'],speaker:['预设音色','Preset voice'],instruct:['表达方式','Delivery instruction'],seed:['随机种子','Seed'],max_new_tokens:['最大生成标记数','Maximum generated tokens'],audio:['参考音频','Reference audio'],reference_text:['参考音频原文','Reference transcript'],prompt:['画面描述 / 编辑指令','Description / edit instruction'],negative_prompt:['避免出现的内容','Negative prompt'],width:['宽度','Width'],height:['高度','Height'],steps:['采样步数','Sampling steps'],megapixels:['图像规模（百万像素）','Image size (megapixels)'],image:['源图片','Source image'],length:['视频帧数','Video frames'],project_name:['已有项目','Existing project'],quality:['渲染质量','Render quality'],filename_prefix:['输出文件名前缀','Output filename prefix']
};
const OPTION_LABELS = {Auto:['自动识别','Automatic'],Chinese:['中文','Chinese'],English:['英语','English'],Japanese:['日语','Japanese'],Korean:['韩语','Korean'],German:['德语','German'],French:['法语','French'],Russian:['俄语','Russian'],Portuguese:['葡萄牙语','Portuguese'],Spanish:['西班牙语','Spanish'],Italian:['意大利语','Italian'],preview:['预览','Preview'],final:['完整品质','Full quality']};
const HELP = {
  reference_text:['请逐字填写参考录音实际说出的内容，示例文字需要替换。','Enter the exact words spoken in the reference recording. Replace the example text.'],
  seed:['相同参数和种子便于对照结果。','Use the same settings and seed to compare results.'],
  max_new_tokens:['限制语音生成长度；过小可能使内容截断。','Limits the generation length. A low value may truncate speech.'],
  length:['帧数影响视频长度与资源使用。','Frame count affects video duration and resource use.'],
  project_name:['使用工作台中已存在的项目。','Use a project that already exists in the studio.']
};

const STORE = 'media-studio.daily.v1';
const LOCAL_GATEWAY = 'http://127.0.0.1:8190';
const ACTIVE = new Set(['pending','running','unknown']);
export function isLoopback(hostname) { const h=hostname.toLowerCase(); return h==='localhost'||h==='[::1]'||/^127(?:\.\d{1,3}){3}$/.test(h); }
export function normalizeGateway(value) {
  let u; try { u=new URL(String(value).trim()); } catch { throw new Error('INVALID_GATEWAY'); }
  if (u.username||u.password||u.search||u.hash||u.pathname!=='/'||!(u.protocol==='https:'||(u.protocol==='http:'&&isLoopback(u.hostname)))) throw new Error('INVALID_GATEWAY');
  return u.origin;
}
export function localizedDefault(profile,field,lang) {
  return field.defaults?.[lang] ?? EXAMPLES[profile]?.[field.name]?.[lang] ?? field.default ?? '';
}
export function createDraft(profile,lang) { return {values:Object.fromEntries(profile.fields.map(f=>[f.name,localizedDefault(profile.key,f,lang)])),dirty:new Set()}; }
export function refreshDraftLocale(profile,draft,lang) { for(const f of profile.fields) if(!draft.dirty.has(f.name)) draft.values[f.name]=localizedDefault(profile.key,f,lang); return draft; }
export function validateValues(profile,values) {
  const errors={};
  for(const f of profile.fields) {
    const v=values[f.name];
    if((v===undefined||v===null||String(v).trim()==='')&&f.required!==false) {errors[f.name]=f.type==='image'||f.type==='audio'?'assetRequired':'required';continue;}
    if((v===''||v==null)&&f.required===false) continue;
    if(f.type==='number'||f.type==='integer') {
      const n=Number(v);
      if(!Number.isFinite(n)||(f.min!=null&&n<f.min)||(f.max!=null&&n>f.max)) errors[f.name]='numberInvalid';
      else if(f.type==='integer'&&!Number.isInteger(n)) errors[f.name]='integerInvalid';
    }
    if(f.type==='select'&&Array.isArray(f.options)&&!f.options.includes(v)) errors[f.name]='optionInvalid';
  }
  return errors;
}
export function queueCount(value) { return Array.isArray(value)?value.length:Math.max(0,Number(value)||0); }
export function cancellationBody(reason) { return reason&&reason!=='user'?'cancelReason':'cancelledBody'; }
export function assetURL(value,gateway) {
  const u=new URL(value,`${gateway}/`);
  if(u.origin!==gateway||u.pathname!=='/api/asset'||u.username||u.password||u.hash) throw new Error('INVALID_ASSET_URL');
  return u.href;
}

function storageGet() {try{return JSON.parse(localStorage.getItem(STORE)||'{}');}catch{return {};}}
const saved=typeof localStorage!=='undefined'?storageGet():{};
let initialGateway=LOCAL_GATEWAY;
if(typeof location!=='undefined'&&location.protocol==='http:'&&isLoopback(location.hostname)) initialGateway=location.origin;
try{if(saved.gateway) initialGateway=normalizeGateway(saved.gateway);}catch{}
const state={lang:saved.lang==='en'?'en':'zh',gateway:initialGateway,catalog:null,drafts:new Map(),profile:'speech',status:null,online:false,connecting:false,job:null,submitting:false,cancelling:false,uploading:new Set(),pending:null,notice:null,mediaIndex:0,mediaKey:'',blobs:new Map(),pollTimer:null,connectionEpoch:0};
const $=s=>document.querySelector(s);
const t=(key,vars={})=>Object.entries(vars).reduce((s,[k,v])=>s.replaceAll(`{${k}}`,String(v)),STRINGS[state.lang][key]??key);
const pair=v=>v?.[state.lang]??'';
const labelPair=v=>v?.[state.lang==='zh'?0:1]??'';
function element(tag,className,text) {const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=text;return n;}
function saveSettings(){try{localStorage.setItem(STORE,JSON.stringify({lang:state.lang,gateway:state.gateway}));}catch{}}
function currentProfile(){return state.catalog?.profiles.find(p=>p.key===state.profile);}
function draftFor(profile){if(!state.drafts.has(profile.key))state.drafts.set(profile.key,createDraft(profile,state.lang));return state.drafts.get(profile.key);}
function errorText(code){return ERRORS[state.lang][code]??ERRORS[state.lang].INTERNAL_ERROR;}
function setNotice(key,kind='info',details=null,isErrorCode=false){state.notice={key,kind,details,isErrorCode};renderNotice();}
function renderNotice(){const n=$('#notice');n.replaceChildren();n.hidden=!state.notice;if(!state.notice)return;n.className=`notice${state.notice.kind==='error'?' is-error':state.notice.kind==='success'?' is-success':''}`;n.append(element('span','',state.notice.isErrorCode?errorText(state.notice.key):t(state.notice.key)));if(state.notice.details){const d=element('details');d.append(element('summary','',t('technicalDetails')),element('pre','',JSON.stringify(state.notice.details,null,2)));n.append(d);}}
function showError(e){setNotice(e.code||e.message||'NETWORK_ERROR','error',e.details??null,true);}
class APIError extends Error {constructor(code,details,status=0){super(code);this.code=code;this.details=details;this.status=status;}}
async function api(path,options={},blob=false){
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),blob?60000:20000);const base=state.gateway;
  try{
    const response=await fetch(new URL(path,`${base}/`),{credentials:'omit',redirect:'error',...options,signal:controller.signal,...(isLoopback(new URL(base).hostname)?{targetAddressSpace:'local'}:{})});
    if(blob){if(!response.ok)throw new APIError('NOT_FOUND',{status:response.status},response.status);return await response.blob();}
    let data;try{data=await response.json();}catch{throw new APIError('UNEXPECTED_RESPONSE',{status:response.status},response.status);}
    if(!response.ok||data.ok!==true)throw new APIError(data.error?.code||'UNEXPECTED_RESPONSE',data.error,response.status);
    return data;
  }catch(e){if(e instanceof APIError)throw e;throw new APIError('NETWORK_ERROR',{name:e.name,message:e.message});}finally{clearTimeout(timeout);}
}
function post(path,body){return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body??{})});}
function busy(){return queueCount(state.status?.queue?.running)+queueCount(state.status?.queue?.pending)>0;}
function setLanguage(lang){
  state.lang=lang==='en'?'en':'zh';saveSettings();
  if(state.catalog)for(const p of state.catalog.profiles)refreshDraftLocale(p,draftFor(p),state.lang);
  renderAll();
}
function translateStatic(){
  document.documentElement.lang=state.lang==='zh'?'zh-CN':'en';document.title=t('brand');
  document.querySelectorAll('[data-i18n]').forEach(n=>{n.textContent=t(n.dataset.i18n);});
  document.querySelectorAll('[data-i18n-aria]').forEach(n=>n.setAttribute('aria-label',t(n.dataset.i18nAria)));
  $('.brand').setAttribute('aria-label',t('brand'));$('#language-select').setAttribute('aria-label',t('language'));$('#language-select').value=state.lang;$('#language-select').options[0].textContent=state.lang==='zh'?'中文':'Chinese';$('#language-select').options[1].textContent=state.lang==='zh'?'英文':'English';$('#profile-nav').setAttribute('aria-label',t('tools'));
  $('#form-hint').textContent=t('formHint');$('#run-help').textContent=t('runHelp');
  // The graph address follows the configured native service only when provided by the gateway.
  const native=state.status?.backend?.client_url;try{const u=new URL(native||'http://127.0.0.1:8188');if(isLoopback(u.hostname)&&u.protocol==='http:')$('#advanced-link').href=u.origin;}catch{}
}
function renderNav(){const nav=$('#profile-nav');nav.replaceChildren();PROFILES.forEach((m,i)=>{
  const p=state.catalog?.profiles.find(x=>x.key===m[0]);const button=element('button',`profile-link${m[0]===state.profile?' is-active':''}`);button.type='button';button.dataset.profile=m[0];button.setAttribute('aria-current',m[0]===state.profile?'page':'false');
  button.append(element('span','nav-number',String(i+1).padStart(2,'0')));const text=element('span','nav-text');const name=element('span','nav-label',pair(p?.label)||m[state.lang==='zh'?1:2]);if(!pair(p?.label)&&(p?.experimental||m[0].startsWith('video')))name.append(element('span','nav-experimental',t('experimental')));text.append(name,element('span','nav-caption',m[state.lang==='zh'?3:4]));button.append(text);button.addEventListener('click',()=>{state.profile=m[0];renderNav();renderForm();});nav.append(button);
});}
function fieldName(f){return pair(f.labels)||labelPair(FIELD_LABELS[f.name])||f.name;}
function optionName(f,v){return pair(f.option_labels?.[v])||labelPair(OPTION_LABELS[v])||v;}
function renderField(profile,f,draft){
  const wrapper=element('div','field');wrapper.dataset.fieldContainer=f.name;
  const id=`field-${profile.key}-${f.name}`;const label=element('label','field-label',fieldName(f));label.htmlFor=id;
  if(f.required===false)label.append(element('span','field-unit',t('optional')));else if(f.min!=null&&f.max!=null)label.append(element('span','field-unit',t('fieldRange',{min:f.min,max:f.max})));
  wrapper.append(label);
  if(f.type==='image'||f.type==='audio'){
    const box=element('div','upload-box');const icon=element('span','upload-icon',f.type==='image'?'▧':'♫');icon.setAttribute('aria-hidden','true');
    const copy=element('div','upload-copy');const chosen=draft.values[f.name];copy.append(element('p','',state.uploading.has(`${profile.key}:${f.name}`)?t('uploading'):chosen||t(f.type==='image'?'imageTypes':'audioTypes')));
    const input=element('input');input.type='file';input.id=id;input.hidden=true;input.accept=f.type==='image'?'.png,.jpg,.jpeg,.webp':'.wav,.flac';input.dataset.field=f.name;input.setAttribute('aria-label',fieldName(f));
    const buttons=element('div','upload-actions');const choose=element('button','text-button',t(f.type==='image'?'chooseImage':'chooseAudio'));choose.type='button';choose.dataset.action='choose-file';choose.disabled=state.uploading.size>0;choose.addEventListener('click',()=>input.click());buttons.append(choose);
    if(chosen){const clear=element('button','text-button',t('clearAsset'));clear.type='button';clear.dataset.action='clear-file';clear.addEventListener('click',()=>{draft.values[f.name]='';draft.dirty.add(f.name);renderForm();});buttons.append(clear);}
    copy.append(buttons);box.append(icon,copy,input);wrapper.append(box);input.addEventListener('change',()=>{if(input.files[0])uploadFile(profile,f,input.files[0]);});
    const samples=state.catalog.assets?.[f.type==='image'?'images':'audio']||[];const select=element('select','sample-select');select.id=`${id}-sample`;select.dataset.field=f.name;select.setAttribute('aria-label',t('chooseSample'));select.append(new Option(t(samples.length?'chooseSample':'noSample'),''));
    for(const sample of samples)select.append(new Option(sample.name,sample.name));select.value=samples.some(s=>s.name===chosen)?chosen:'';select.addEventListener('change',()=>{if(select.value){draft.values[f.name]=select.value;draft.dirty.add(f.name);renderForm();}});select.disabled=samples.length===0;wrapper.append(select);
  }else{
    const input=element(f.type==='textarea'?'textarea':f.type==='select'?'select':'input');input.id=id;input.dataset.field=f.name;input.name=f.name;
    if(f.type==='textarea'){input.rows=f.name==='negative_prompt'||f.name==='instruct'?3:6;if(f.name==='negative_prompt'||f.name==='instruct')input.className='is-secondary';}
    else if(f.type==='select'){for(const v of f.options||[])input.append(new Option(optionName(f,v),v));}
    else {input.type=f.type==='integer'||f.type==='number'?'number':'text';if(f.min!=null)input.min=f.min;if(f.max!=null)input.max=f.max;if(f.type==='integer')input.step='1';else if(f.type==='number')input.step=f.step??'any';}
    input.value=draft.values[f.name]??'';if(f.name==='reference_text')input.placeholder=labelPair(HELP.reference_text);input.required=f.required!==false;input.addEventListener('input',()=>{draft.values[f.name]=input.type==='number'&&input.value!==''?Number(input.value):input.value;draft.dirty.add(f.name);input.removeAttribute('aria-invalid');const error=wrapper.querySelector('.field-error');if(error)error.remove();});wrapper.append(input);
  }
  const help=labelPair(HELP[f.name])||pair(f.description);if(help&&help.trim()!==fieldName(f).trim()){const note=element('p','field-help',help);note.id=`${id}-help`;wrapper.append(note);wrapper.querySelector(`#${CSS.escape(id)}`)?.setAttribute('aria-describedby',note.id);}
  return wrapper;
}
function renderForm(){
  const p=currentProfile(),meta=PROFILES.find(m=>m[0]===state.profile);$('#profile-number').textContent=String(PROFILES.indexOf(meta)+1).padStart(2,'0');$('#profile-title').textContent=pair(p?.label)||meta[state.lang==='zh'?1:2];$('#profile-badge').textContent=meta[5];$('#profile-description').textContent=pair(p?.description)||(state.connecting?t('catalogLoading'):t('catalogMissing'));
  $('#profile-warning').hidden=!(p?.experimental||state.profile.startsWith('video'));$('#profile-warning').textContent=t('videoWarning');const fields=$('#form-fields');fields.replaceChildren();
  if(!p)fields.append(element('p','resource-offline',t(state.connecting?'catalogLoading':'catalogMissing')));
  else {const draft=draftFor(p);let row=null;for(const f of p.fields){const compact=f.type==='integer'||f.type==='number'||f.type==='select';if(compact){if(!row||row.childElementCount===2){row=element('div','field-row');fields.append(row);}row.append(renderField(p,f,draft));}else{row=null;fields.append(renderField(p,f,draft));}}}
  $('#example-button').hidden=!EXAMPLES[state.profile];updateControls();
}
function updateControls(){
  const active=state.job&&ACTIVE.has(state.job.status);const unavailable=!state.online||!state.status?.backend?.online||!currentProfile();const locked=state.submitting||state.uploading.size>0;
  $('#run-button').disabled=locked||unavailable||(!state.pending&&(busy()||active));$('#run-label').textContent=t(state.submitting?'submitting':state.pending?'retry':'run');$('#example-button').disabled=locked||!!state.pending;document.body.classList.toggle('is-submitting',state.submitting);
  // A request with an uncertain response must retain the exact payload for a safe retry.
  $('#form-fields').querySelectorAll('input,textarea,select,button').forEach(n=>{if(state.pending)n.disabled=true;else if(!n.classList.contains('sample-select')||n.options.length>1)n.disabled=locked;});
  $('#free-button').disabled=!state.online||!state.status?.backend?.online||busy()||state.submitting;$('#refresh-button').disabled=state.connecting;
  $('#profile-nav').querySelectorAll('button').forEach(n=>{n.disabled=state.submitting||!!state.pending;});
}
function renderResources(){
  const b=$('#connection-button');const healthy=state.online&&state.status?.backend?.online;const title=state.connecting?'connecting':!state.online?'offline':!healthy?'backendOffline':busy()?'busy':'connected';$('#connection-label').textContent=t(title);b.classList.toggle('is-online',!!healthy);b.classList.toggle('is-busy',busy());b.setAttribute('aria-label',`${t(title)}. ${t('connectionSettings')}`);b.title=t(title);
  const area=$('#resource-content');area.replaceChildren();
  if(!state.online||!state.status){area.append(element('p','resource-offline',t('resourcesOffline')));$('#idle-status').textContent='';updateControls();return;}
  const r=state.status.resources||{},grid=element('div','resource-grid');
  const stat=(key,bytes)=>{const n=element('div','resource-stat');n.append(element('span','',t(key)));const strong=element('strong','',Number.isFinite(bytes)?(bytes/1073741824).toFixed(1):t('unavailable'));if(Number.isFinite(bytes))strong.append(element('small','','GiB'));n.append(strong);grid.append(n);};stat('available',r.available_bytes);stat('headroom',r.commit_headroom_bytes);
  const commit=element('div','resource-stat full');commit.append(element('span','',t('commit')));const value=element('strong','',Number.isFinite(r.commit_percent)?`${r.commit_percent.toFixed(0)}%`:t('unavailable'));commit.append(value);grid.append(commit);area.append(grid);
  if(Number.isFinite(r.commit_percent)){const meter=element('div',`resource-meter${r.commit_percent>=90?' is-warning':''}`);const bar=element('span');bar.style.width=`${Math.min(100,Math.max(0,r.commit_percent))}%`;meter.append(bar);area.append(meter);}
  const devices=r.gpu?.devices||r.gpu?.system_stats?.devices;if(Array.isArray(devices)){const gpu=devices.find(d=>Number.isFinite(d.vram_free));if(gpu)stat('gpu',gpu.vram_free);}
  const q=element('div','queue-line');q.append(element('span','',t('queue')),element('span','',t('queueValue',{running:queueCount(state.status.queue?.running),pending:queueCount(state.status.queue?.pending)})));area.append(q,element('p','resource-footnote',t('resourceNote')));
  const idle=state.status.idle_free;$('#idle-status').textContent=idle?.armed?t('idleArmed',{seconds:idle.seconds??30}):idle?.last_freed_at?t('lastFreed'):t('idleReady');updateControls();
}
function clearBlobs(){for(const url of state.blobs.values())URL.revokeObjectURL(url);state.blobs.clear();}
function adoptJob(job){if(!job?.id)return;if(state.job?.id===job.id&&job.status!=='unknown')state.pending=null;if(state.job?.id!==job.id){clearBlobs();state.mediaIndex=0;state.mediaKey='';}state.job=job;renderResult();updateControls();}
function emptyResult(title,body,working=false){const n=element('div','empty-result');if(working)n.append(element('span','working-mark'));else{const mark=element('span','', '◈');mark.setAttribute('aria-hidden','true');mark.style.cssText='font-size:32px;line-height:1;margin-bottom:18px;color:#97aba2';n.append(mark);}n.append(element('h3','',t(title)),element('p','',t(body)));return n;}
function renderResult(force=false){
  const job=state.job;const status=job?.status||'empty';$('#job-status').textContent=t({pending:'taskPending',running:'taskRunning',success:'taskSuccess',error:'taskError',cancelled:'taskCancelled',unknown:'taskUnknown',empty:'taskEmpty'}[status]||'unknownStatus');$('#job-status').className=`state-label${status==='success'?' is-success':status==='error'?' is-error':ACTIVE.has(status)?' is-running':''}`;
  const area=$('#result-content'),actions=$('#job-actions');const outputs=job?.outputs||[];const key=`${state.lang}:${job?.id}:${status}:${state.mediaIndex}:${JSON.stringify(outputs)}`;
  if(key===state.mediaKey&&!force)return;state.mediaKey=key;area.replaceChildren();actions.replaceChildren();$('#technical-details').hidden=!job;$('#technical-content').textContent=job?JSON.stringify({prompt_id:job.prompt_id||job.id,status:job.status,error:job.error,cancel_reason:job.cancel_reason,created_at:job.created_at,updated_at:job.updated_at},null,2):'';
  if(!job)area.append(emptyResult('emptyTitle','emptyBody'));
  else if(status==='success'&&outputs.length){const output=outputs[Math.min(state.mediaIndex,outputs.length-1)];const holder=element('div');holder.append(element('p','resource-offline',t('mediaLoading')));area.append(holder);loadMedia(output,holder,key);if(outputs.length>1){const pages=element('div','result-pager');outputs.forEach((o,i)=>{const button=element('button',i===state.mediaIndex?'is-active':'',String(i+1));button.type='button';button.setAttribute('aria-label',t('outputNumber',{number:i+1}));button.addEventListener('click',()=>{state.mediaIndex=i;renderResult();});pages.append(button);});area.append(pages);}}
  else if(status==='success')area.append(emptyResult('errorTitle','noOutput'));
  else if(status==='running')area.append(emptyResult('workingTitle','workingBody',true));
  else if(status==='pending')area.append(emptyResult('pendingTitle','pendingBody',true));
  else if(status==='unknown')area.append(emptyResult('unknownTitle','unknownBody'));
  else if(status==='cancelled')area.append(emptyResult('cancelledTitle',cancellationBody(job.cancel_reason)));
  else{const n=emptyResult('errorTitle','noOutput');n.querySelector('p').textContent=errorText(job.error?.code||'EXECUTION_ERROR');area.append(n);}
  if(job&&['pending','running'].includes(status)){const row=element('div','result-actions');const cancel=element('button','cancel-button',t(state.cancelling?'cancelling':'cancel'));cancel.id='cancel-job-button';cancel.type='button';cancel.disabled=state.cancelling;cancel.addEventListener('click',cancelJob);row.append(cancel);actions.append(row);}
  if(job)actions.append(element('p','job-reference',`${t('jobReference')} · ${job.id}`));
}
async function loadMedia(output,holder,key){
  try{const url=assetURL(output.url,state.gateway);let objectURL=state.blobs.get(url);if(!objectURL){const blob=await api(url,{},true);const allowed={image:/^image\/(png|jpeg|webp|gif)$/,audio:/^audio\/(wav|x-wav|flac|x-flac|mpeg|ogg|mp4)$/,video:/^video\/(mp4|webm)$/};if(!allowed[output.kind]?.test(blob.type.split(';')[0]))throw new APIError('UNSUPPORTED_MEDIA',{mime:blob.type});if(state.mediaKey!==key)return;objectURL=URL.createObjectURL(blob);state.blobs.set(url,objectURL);}
    if(state.mediaKey!==key)return;holder.replaceChildren();const media=element(output.kind==='image'?'img':output.kind);media.src=objectURL;if(output.kind==='image')media.alt=t('localPreview');else{media.controls=true;media.preload='metadata';if(output.kind==='video')media.playsInline=true;}media.addEventListener('error',()=>{holder.append(element('p','field-error',t('renderFailure')));},{once:true});const frame=element('div','result-media');frame.append(media);holder.append(frame,element('p','result-caption',output.name));const row=element('div','result-actions');const download=element('a','',t('download'));download.href=objectURL;download.download=output.name?.split(/[\\/]/).pop()||'output';row.append(download);holder.append(row);
  }catch(e){if(state.mediaKey!==key)return;holder.replaceChildren(element('p','field-error',e.code?errorText(e.code):t('mediaUnavailable')));const button=element('button','text-button',t('retryMedia'));button.type='button';button.addEventListener('click',()=>renderResult(true));holder.append(button);}
}
async function uploadFile(profile,field,file){
  const ext=file.name.split('.').pop().toLowerCase();if(!(field.type==='image'?['png','jpg','jpeg','webp']:['wav','flac']).includes(ext)){showError(new APIError('UPLOAD_TYPE'));return;}
  if(file.size>(state.catalog?.limits?.upload_bytes??33554432)){showError(new APIError('UPLOAD_TOO_LARGE'));return;}
  const key=`${profile.key}:${field.name}`,epoch=state.connectionEpoch;state.uploading.add(key);renderForm();
  try{const body=new FormData();body.append('file',file);const data=await api('/api/upload',{method:'POST',body});if(epoch!==state.connectionEpoch)return;if(data.asset?.kind!==field.type||!data.asset.name)throw new APIError('UNEXPECTED_RESPONSE');assetURL(data.asset.url,state.gateway);const draft=draftFor(profile);draft.values[field.name]=data.asset.name;draft.dirty.add(field.name);state.notice=null;renderNotice();}
  catch(e){if(epoch===state.connectionEpoch)showError(e);}finally{state.uploading.delete(key);renderForm();}
}
function displayValidation(profile,errors){for(const [name,key]of Object.entries(errors)){const field=$(`[data-field-container="${name}"]`);field?.querySelector('input,select,textarea')?.setAttribute('aria-invalid','true');field?.append(element('p','field-error',t(key)));}const first=Object.keys(errors)[0];if(first)$(`[data-field-container="${first}"] input,[data-field-container="${first}"] textarea,[data-field-container="${first}"] select`)?.focus();}
function requestID(){return crypto.randomUUID();}
async function submit(event){
  event.preventDefault();if(state.submitting||state.uploading.size)return;const p=currentProfile();if(!p)return;
  if(!state.pending){const draft=draftFor(p),errors=validateValues(p,draft.values);document.querySelectorAll('.field-error').forEach(n=>{if(n.closest('#form-fields'))n.remove();});if(Object.keys(errors).length){displayValidation(p,errors);return;}state.pending={profile:p.key,values:{...draft.values},request_id:requestID()};}
  state.submitting=true;updateControls();
  try{const data=await post('/api/run',state.pending);if(!data.job?.id)throw new APIError('UNEXPECTED_RESPONSE');if(data.job.status!=='unknown')state.pending=null;state.notice=null;renderNotice();adoptJob(data.job);await refreshStatus();}
  catch(e){const uncertain=e.code==='NETWORK_ERROR'||e.code==='SUBMISSION_UNCERTAIN'||e.code==='UNEXPECTED_RESPONSE'||e.status>=500&&e.code!=='RELEASE_PENDING';if(!uncertain)state.pending=null;showError(e);}
  finally{state.submitting=false;updateControls();}
}
async function cancelJob(){if(state.cancelling||!state.job||!['pending','running'].includes(state.job.status))return;state.cancelling=true;renderResult(true);try{const data=await post(`/api/jobs/${encodeURIComponent(state.job.id)}/cancel`);adoptJob(data.job);setNotice('cancelRequested');}catch(e){showError(e);}finally{state.cancelling=false;renderResult(true);}}
async function release(){const button=$('#free-button');button.disabled=true;try{const data=await post('/api/free');setNotice(data.observed_stable?'releaseRequested':'releasedUnknown','success');await refreshStatus();}catch(e){showError(e);}finally{updateControls();}}
async function refreshStatus(){const epoch=state.connectionEpoch;try{const data=await api('/api/status');if(epoch!==state.connectionEpoch)return;state.status=data;state.online=true;if(!state.job&&data.active_job)adoptJob(data.active_job);renderResources();}catch(e){if(epoch!==state.connectionEpoch)return;state.online=false;renderResources();throw e;}}
async function poll(){clearTimeout(state.pollTimer);if(!state.catalog){await connect();return;}try{await refreshStatus();if(state.job&&ACTIVE.has(state.job.status)){const data=await api(`/api/jobs/${encodeURIComponent(state.job.id)}`);adoptJob(data.job);}}catch{}finally{state.pollTimer=setTimeout(poll,4000);}}
async function connect(){
  state.connectionEpoch++;const epoch=state.connectionEpoch;clearTimeout(state.pollTimer);state.connecting=true;state.online=false;renderAll();
  const results=await Promise.allSettled([api('/api/catalog'),api('/api/status')]);if(epoch!==state.connectionEpoch)return;
  const catalog=results[0],status=results[1];if(catalog.status==='fulfilled'&&Array.isArray(catalog.value.profiles)){state.catalog=catalog.value;for(const p of state.catalog.profiles){if(!state.drafts.has(p.key))state.drafts.set(p.key,createDraft(p,state.lang));}}
  if(status.status==='fulfilled'){state.status=status.value;state.online=true;if(!state.job&&status.value.active_job)adoptJob(status.value.active_job);}else{state.status=null;state.online=false;showError(status.reason);}
  if(catalog.status==='rejected')showError(catalog.reason);state.connecting=false;renderAll();state.pollTimer=setTimeout(poll,4000);
}
function renderAll(){translateStatic();renderNav();renderForm();renderResources();renderNotice();renderResult(true);}
function openSettings(){$('#gateway-url').value=state.gateway;$('#settings-error').hidden=true;$('#settings-dialog').showModal();}
function init(){
  $('#language-select').addEventListener('change',e=>setLanguage(e.target.value));$('#settings-button').addEventListener('click',openSettings);$('#connection-button').addEventListener('click',openSettings);$('#close-settings').addEventListener('click',()=>$('#settings-dialog').close());$('#reset-gateway').addEventListener('click',()=>{$('#gateway-url').value=LOCAL_GATEWAY;});
  $('#settings-form').addEventListener('submit',e=>{e.preventDefault();try{const gateway=normalizeGateway($('#gateway-url').value);if(gateway!==state.gateway){clearBlobs();state.job=null;state.mediaKey='';state.pending=null;state.status=null;state.catalog=null;state.drafts.clear();}state.gateway=gateway;saveSettings();$('#settings-dialog').close();setNotice('newConnection');connect();}catch{$('#settings-error').textContent=errorText('INVALID_GATEWAY');$('#settings-error').hidden=false;}});
  $('#refresh-button').addEventListener('click',async()=>{try{await refreshStatus();renderResult(true);}catch(e){showError(e);}});$('#free-button').addEventListener('click',release);$('#creation-form').addEventListener('submit',submit);$('#example-button').addEventListener('click',()=>{const p=currentProfile();if(!p)return;const d=draftFor(p);for(const name of Object.keys(EXAMPLES[p.key]||{})){const f=p.fields.find(x=>x.name===name);if(f){d.values[name]=localizedDefault(p.key,f,state.lang);d.dirty.delete(name);}}renderForm();});window.addEventListener('pagehide',()=>{clearTimeout(state.pollTimer);clearBlobs();});renderAll();connect();
}
if(typeof document!=='undefined')init();
