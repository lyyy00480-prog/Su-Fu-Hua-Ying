import pygame, sys, os, json, math, random
import pygame.mixer
from core.asset_manager import AssetManager

def get_resource_path(p):
    if hasattr(sys,'_MEIPASS'): return os.path.join(sys._MEIPASS,p)
    return os.path.join(os.path.abspath('.'),p)

pygame.init(); pygame.mixer.init()
SCREEN_WIDTH=800; SCREEN_HEIGHT=600
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption('苏府画影')
clock=pygame.time.Clock(); FPS=60

WHITE=(255,255,255); BLACK=(0,0,0)
PURPLE_DEEP=(58,10,90); PURPLE_MID=(110,40,160)
PURPLE_LIGHT=(180,120,220); PURPLE_PALE=(220,180,255)
GOLD=(255,200,80); PAPER=(245,238,220); PAPER_WARM=(255,248,230); INK=(30,20,50)

asset_manager=AssetManager(os.path.join('data','assets_config.json'))
sfx_cache={}
img_cache={}

def _load_font(size):
    try:
        p=asset_manager.get_asset_path('FONT_chinese_dialogue')
        if os.path.exists(p) and os.path.getsize(p)>0: return pygame.font.Font(p,size)
    except: pass
    return pygame.font.Font(None,size)

font_title=_load_font(64); font_btn=_load_font(32); font_small=_load_font(22)
font_speaker=_load_font(30); font_dialogue=_load_font(26)
font_option=_load_font(27); font_sketch=_load_font(24)

STATE_MENU='MENU'; STATE_PLAYING='PLAYING'
STATE_SKETCHBOOK='SKETCHBOOK'; STATE_CREDITS='CREDITS'
current_state=STATE_MENU

DLG_RECT=pygame.Rect(20,430,760,150)
DLG_PAD_X=22; DLG_PAD_Y=16; DLG_LINE_SP=6; TYPE_DELAY=30

def scale_image(image,tw,th):
    iw,ih=image.get_size(); s=max(tw/iw,th/ih)
    nw,nh=int(iw*s),int(ih*s)
    scaled=pygame.transform.scale(image,(nw,nh))
    cx,cy=(nw-tw)//2,(nh-th)//2
    return scaled.subsurface((cx,cy,tw,th))

def load_bg(asset_id):
    try:
        p=asset_manager.get_asset_path(asset_id)
        img=pygame.image.load(p).convert_alpha()
        return scale_image(img,SCREEN_WIDTH,SCREEN_HEIGHT)
    except Exception as e:
        print(f'load_bg error {asset_id}: {e}')
        s=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT)); s.fill(PURPLE_DEEP); return s

def load_asset_image(asset_id):
    """加载原始素材图（不裁剪），用于速写本/缩略图等场景。"""
    if asset_id in img_cache:
        return img_cache[asset_id]
    try:
        p=asset_manager.get_asset_path(asset_id)
        img=pygame.image.load(p).convert_alpha()
        img_cache[asset_id]=img
        return img
    except Exception as e:
        print(f'load_asset_image error {asset_id}: {e}')
        s=pygame.Surface((16,16),pygame.SRCALPHA)
        s.fill((0,0,0,0))
        img_cache[asset_id]=s
        return s

def play_sfx(sfx_id):
    if sfx_id not in sfx_cache:
        try:
            p=asset_manager.get_asset_path(sfx_id)
            if os.path.exists(p) and os.path.getsize(p)>0: sfx_cache[sfx_id]=pygame.mixer.Sound(p)
        except: return
    if sfx_id in sfx_cache: sfx_cache[sfx_id].play()

def wrap_text(text,font,max_width):
    lines2=[]; line=''
    for ch in text:
        test=line+ch
        if font.size(test)[0]>max_width:
            if line: lines2.append(line)
            line=ch
        else: line=test
    if line: lines2.append(line)
    return lines2

try:
    with open(get_resource_path(os.path.join('data','script.json')),'r',encoding='utf-8') as f:
        dialogues=json.load(f)
except Exception as e:
    print(f'script.json error: {e}')
    dialogues=[{'speaker':'林墨','text':'剧本加载失败。','background':'scene_old_house'}]

try:
    with open(get_resource_path(os.path.join('data','credits.json')),'r',encoding='utf-8') as f:
        CREDITS_LINES=json.load(f)['credits']
except: CREDITS_LINES=['感谢游玩','','苏府画影']

SKETCHBOOK_SAVE_PATH=get_resource_path(os.path.join('data','save_sketchbook.json'))
collected_cgs=[]  # list[dict]: { "key": str, "bg_id": str, "title": str, "comment": str }

def load_sketchbook_save():
    global collected_cgs
    try:
        if os.path.exists(SKETCHBOOK_SAVE_PATH):
            with open(SKETCHBOOK_SAVE_PATH,'r',encoding='utf-8') as f:
                data=json.load(f)
            items=data.get('items',[])
            if isinstance(items,list):
                collected_cgs=items
                # 迁移：把旧存档里固定同一句画评替换为按 script 内容生成的画评
                old_default='林墨：我把这张画收进速写本里了。'
                changed=False
                for it in collected_cgs:
                    if not isinstance(it,dict): 
                        continue
                    k=it.get('key','')
                    if not isinstance(k,str): 
                        continue
                    parts=k.split(':')
                    if len(parts)>=3 and parts[0]=='第一章':
                        try:
                            idx=int(parts[1])
                        except:
                            continue
                        if not it.get('comment') or it.get('comment')==old_default:
                            it['comment']=make_comment_from_dialogue_idx(idx)
                            changed=True
                if changed:
                    save_sketchbook_save()
        else:
            # 首次运行创建空存档，避免“进入速写本没有读档文件”的感觉
            save_sketchbook_save()
    except Exception as e:
        print(f'load_sketchbook_save error: {e}')

def save_sketchbook_save():
    try:
        os.makedirs(os.path.dirname(SKETCHBOOK_SAVE_PATH),exist_ok=True)
        with open(SKETCHBOOK_SAVE_PATH,'w',encoding='utf-8') as f:
            json.dump({'items':collected_cgs},f,ensure_ascii=False,indent=2)
    except Exception as e:
        print(f'save_sketchbook_save error: {e}')

def make_comment_from_dialogue_idx(idx):
    """根据 script.json 的对话文本生成速写本画评（避免固定同一句）。"""
    old_default='林墨：我把这张画收进速写本里了。'
    try:
        if not isinstance(idx,int) or idx<0 or idx>=len(dialogues): 
            return old_default
        entry=dialogues[idx] if idx < len(dialogues) else {}
        text=entry.get('text','')
        if not isinstance(text,str): 
            return old_default
        s=text.replace('\n','').strip()
        if not s: 
            return old_default
        # 截取一小段，控制字数，避免 UI 文字溢出
        if len(s)>11:
            s=s[:11]+'…'
        return f'林墨：{s}'
    except Exception:
        return old_default

def collect_cg(bg_id,title='未命名 CG',comment=''):
    if not isinstance(bg_id,str) or not bg_id: 
        return
    key=f'{len(dialogues)}:{bg_id}:{title}:{comment}'
    # 兼容旧逻辑：如果已有同名同图同评就不重复收
    for it in collected_cgs:
        if isinstance(it,dict) and it.get('bg_id')==bg_id and it.get('title')==title and it.get('comment')==comment:
            return
    collected_cgs.append({'key':key,'bg_id':bg_id,'title':title,'comment':comment})
    save_sketchbook_save()

def collect_cg_by_index(idx,bg_id,chapter='第一章'):
    """按对话序号收集，避免同一背景只剩两张的问题。"""
    if not isinstance(idx,int): 
        return
    key=f'{chapter}:{idx}:{bg_id}'
    for it in collected_cgs:
        if isinstance(it,dict) and it.get('key')==key:
            return
    title=f'{chapter} · 片段 {idx+1}'
    comment=make_comment_from_dialogue_idx(idx)
    collected_cgs.append({'key':key,'bg_id':bg_id,'title':title,'comment':comment})
    save_sketchbook_save()

# 启动时先读档
load_sketchbook_save()

class Particle:
    def __init__(self): self.reset()
    def reset(self):
        edge=random.randint(0,3)
        if edge==0: self.x,self.y=random.uniform(0,SCREEN_WIDTH),random.uniform(0,60)
        elif edge==1: self.x,self.y=random.uniform(0,SCREEN_WIDTH),random.uniform(SCREEN_HEIGHT-60,SCREEN_HEIGHT)
        elif edge==2: self.x,self.y=random.uniform(0,60),random.uniform(0,SCREEN_HEIGHT)
        else: self.x,self.y=random.uniform(SCREEN_WIDTH-60,SCREEN_WIDTH),random.uniform(0,SCREEN_HEIGHT)
        speed=random.uniform(30,90); angle=random.uniform(0,math.pi*2)
        self.vx=math.cos(angle)*speed*0.3; self.vy=math.sin(angle)*speed*0.3-speed*0.6
        self.life=self.max_life=random.uniform(0.6,1.4); self.radius=random.uniform(2,5)
        self.color=random.choice([PURPLE_LIGHT,PURPLE_PALE,(200,160,255),(240,200,255)])
    def update(self,dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt; self.vy+=20*dt; self.life-=dt
        return self.life>0
    def draw(self,surf):
        alpha=max(0,int(255*(self.life/self.max_life)))
        r=max(1,int(self.radius*(self.life/self.max_life)))
        s=pygame.Surface((r*2+2,r*2+2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.color,alpha),(r+1,r+1),r)
        surf.blit(s,(int(self.x)-r-1,int(self.y)-r-1))

particles=[]; particle_active=False; particle_timer=0.0; PARTICLE_DURATION=2.2

def trigger_particles():
    global particle_active,particle_timer,particles
    particle_active=True; particle_timer=0.0
    particles=[Particle() for _ in range(80)]

def update_particles(dt):
    global particle_active,particle_timer
    if not particle_active: return
    particle_timer+=dt
    if particle_timer>PARTICLE_DURATION:
        particle_active=False; particles.clear(); return
    if particle_timer<PARTICLE_DURATION*0.5 and random.random()<0.4:
        particles.append(Particle())
    particles[:]=[p for p in particles if p.update(dt)]

def draw_particles(surf):
    for p in particles: p.draw(surf)

def draw_dusk_sky(surf,t):
    colors=[(30,5,60),(80,20,110),(140,50,130),(200,80,90),(230,130,60),(240,180,80)]
    n=len(colors)-1
    for i in range(n):
        y0=int(SCREEN_HEIGHT*i/n); y1=int(SCREEN_HEIGHT*(i+1)/n)
        c0,c1=colors[i],colors[i+1]
        for y in range(y0,y1):
            ratio=(y-y0)/max(1,y1-y0)
            pygame.draw.line(surf,(
                int(c0[0]+(c1[0]-c0[0])*ratio),
                int(c0[1]+(c1[1]-c0[1])*ratio),
                int(c0[2]+(c1[2]-c0[2])*ratio)
            ),(0,y),(SCREEN_WIDTH,y))
    for i in range(3):
        phase=t*0.3+i*2.1
        cx=int(SCREEN_WIDTH*(0.2+0.6*((math.sin(phase)+1)/2)))
        cy=int(SCREEN_HEIGHT*(0.3+0.15*math.sin(phase*0.7+i)))
        for radius in range(120,0,-20):
            alpha=int(18*(1-radius/120))
            gs=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
            col=(180,80,200,alpha) if i==0 else (220,120,60,alpha) if i==1 else (255,200,80,alpha)
            pygame.draw.circle(gs,col,(radius,radius),radius)
            surf.blit(gs,(cx-radius,cy-radius))
    random.seed(42)
    for i in range(30):
        sx=random.randint(0,SCREEN_WIDTH); sy=random.randint(0,int(SCREEN_HEIGHT*0.55))
        alpha=int(80+120*abs(math.sin(t*1.5+i*0.7))); r=random.randint(1,3)
        ss=pygame.Surface((r*2+2,r*2+2),pygame.SRCALPHA)
        pygame.draw.circle(ss,(255,230,200,min(255,alpha)),(r+1,r+1),r)
        surf.blit(ss,(sx-r-1,sy-r-1))
    random.seed()

class Button:
    def __init__(self,label,cx,cy,w=220,h=52):
        self.label=label; self.rect=pygame.Rect(cx-w//2,cy-h//2,w,h)
        self.hovered=False; self._hover_t=0.0
    def update(self,dt,mp):
        self.hovered=self.rect.collidepoint(mp)
        self._hover_t=min(1.0,self._hover_t+dt*5) if self.hovered else max(0.0,self._hover_t-dt*5)
    def is_clicked(self,event):
        return event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(event.pos)
    def draw(self,surf):
        h=self._hover_t
        sh=pygame.Surface((self.rect.w+6,self.rect.h+6),pygame.SRCALPHA)
        pygame.draw.rect(sh,(0,0,0,60),(0,0,self.rect.w+6,self.rect.h+6),border_radius=10)
        surf.blit(sh,(self.rect.x+2,self.rect.y+5))
        fc=(int(PURPLE_DEEP[0]+(PURPLE_MID[0]-PURPLE_DEEP[0])*h),int(PURPLE_DEEP[1]+(PURPLE_MID[1]-PURPLE_DEEP[1])*h),int(PURPLE_DEEP[2]+(PURPLE_MID[2]-PURPLE_DEEP[2])*h))
        bs=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
        pygame.draw.rect(bs,(*fc,200),(0,0,self.rect.w,self.rect.h),border_radius=8)
        surf.blit(bs,self.rect.topleft)
        pygame.draw.rect(surf,PURPLE_PALE if h>0.5 else PURPLE_LIGHT,self.rect,2,border_radius=8)
        surf.blit(font_btn.render(self.label,True,GOLD if h>0.5 else WHITE),font_btn.render(self.label,True,WHITE).get_rect(center=self.rect.center))
        if h>0.1:
            uw=int(self.rect.w*0.6*h); ux=self.rect.centerx-uw//2
            pygame.draw.line(surf,GOLD,(ux,self.rect.bottom-8),(ux+uw,self.rect.bottom-8),2)

class MenuState:
    def __init__(self):
        self._t=0.0; cx=SCREEN_WIDTH//2
        self.buttons=[Button('开始游戏',cx,340),Button('速写本',cx,410),Button('关于我们',cx,480)]
    def enter(self):
        self._t=0.0
        try:
            p=asset_manager.get_asset_path('AUDIO_menu_bgm')
            if os.path.exists(p): pygame.mixer.music.load(p); pygame.mixer.music.play(-1)
        except: pass
    def handle_event(self,event):
        global current_state
        for i,btn in enumerate(self.buttons):
            if btn.is_clicked(event):
                pygame.mixer.music.stop()
                if i==0: playing_state.reset(); current_state=STATE_PLAYING
                elif i==1: sketchbook_state.enter(); current_state=STATE_SKETCHBOOK
                elif i==2: credits_state.enter(); current_state=STATE_CREDITS
    def update(self,dt):
        self._t+=dt
        for btn in self.buttons: btn.update(dt,pygame.mouse.get_pos())
    def draw(self,surf):
        draw_dusk_sky(surf,self._t)
        glow=pygame.Surface((400,100),pygame.SRCALPHA)
        for r in range(50,0,-10): pygame.draw.ellipse(glow,(180,80,220,int(12*(1-r/50))),(200-r*4,50-r,r*8,r*2))
        surf.blit(glow,(SCREEN_WIDTH//2-200,120))
        ts2=font_title.render('苏府画影',True,PURPLE_PALE)
        ts=font_title.render('苏府画影',True,WHITE)
        surf.blit(ts2,ts2.get_rect(center=(SCREEN_WIDTH//2+2,202)))
        surf.blit(ts,ts.get_rect(center=(SCREEN_WIDTH//2,200)))
        sub=font_small.render('— 一段关于紫色与画笔的故事 —',True,PURPLE_PALE)
        surf.blit(sub,sub.get_rect(center=(SCREEN_WIDTH//2,258)))
        for btn in self.buttons: btn.draw(surf)
        ver=font_small.render('Chapter I  Demo',True,(180,140,200))
        surf.blit(ver,ver.get_rect(bottomright=(SCREEN_WIDTH-15,SCREEN_HEIGHT-10)))

class SketchbookState:
    PAGE_W=560; PAGE_H=400
    def __init__(self): self.page=0
    def enter(self):
        # 进入速写本时读档（避免每次看起来“重置”）
        load_sketchbook_save()
        self.page=max(0,min(self.page,self._max()-1))
    def _max(self): return max(1,len(collected_cgs))
    def handle_event(self,event):
        global current_state
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: current_state=STATE_MENU; menu_state.enter()
            elif event.key in (pygame.K_RIGHT,pygame.K_d) and self.page<self._max()-1: self.page+=1
            elif event.key in (pygame.K_LEFT,pygame.K_a) and self.page>0: self.page-=1
        if event.type==pygame.MOUSEBUTTONDOWN:
            if event.button==3: current_state=STATE_MENU; menu_state.enter()
            elif event.button==1:
                if event.pos[0]>SCREEN_WIDTH//2+180 and self.page<self._max()-1: self.page+=1
                elif event.pos[0]<SCREEN_WIDTH//2-180 and self.page>0: self.page-=1
    def update(self,dt): pass
    def draw(self,surf):
        draw_dusk_sky(surf,pygame.time.get_ticks()/1000.0)
        dim=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
        dim.fill((0,0,0,100)); surf.blit(dim,(0,0))
        pw,ph=self.PAGE_W,self.PAGE_H
        rx=(SCREEN_WIDTH-pw)//2; ry=(SCREEN_HEIGHT-ph)//2
        sh=pygame.Surface((pw+16,ph+16),pygame.SRCALPHA)
        pygame.draw.rect(sh,(0,0,0,70),(0,0,pw+16,ph+16),border_radius=6)
        surf.blit(sh,(rx-8,ry+8))
        pg=pygame.Surface((pw,ph)); pg.fill(PAPER_WARM)
        for ly in range(36,ph,22): pygame.draw.line(pg,(200,190,170,80),(20,ly),(pw-20,ly),1)
        for sx in range(18): pygame.draw.line(pg,(100,60,100,int(40*(1-sx/18))),(sx,0),(sx,ph))
        pygame.draw.rect(pg,(180,160,140),(0,0,pw,ph),2,border_radius=4)
        surf.blit(pg,(rx,ry))
        if not collected_cgs:
            m=font_sketch.render('速写本暂无收藏',True,(160,140,120))
            m2=font_small.render('游戏中的 CG 画面将自动收入此处',True,(180,160,140))
            surf.blit(m,m.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-20)))
            surf.blit(m2,m2.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+20)))
        else:
            # 防止收藏数量变化导致页码越界
            if self.page>len(collected_cgs)-1: self.page=max(0,len(collected_cgs)-1)
            it=collected_cgs[self.page] if self.page < len(collected_cgs) else {}
            bg_id=it.get('bg_id','') if isinstance(it,dict) else ''
            display_title=(it.get('title','未命名 CG') if isinstance(it,dict) else '未命名 CG')
            comment=(it.get('comment','林墨：我把这张画收进速写本里了。') if isinstance(it,dict) else '林墨：我把这张画收进速写本里了。')
            try:
                # 速写本用原图等比缩放，避免背景裁剪后的二次失真
                cg=load_asset_image(bg_id)
                iw,ih=cg.get_size()
                max_w=pw-60
                max_h=ph-110  # 预留底部两行文字空间
                if iw>0 and ih>0:
                    s=min(max_w/iw,max_h/ih)
                    nw,nh=max(1,int(iw*s)),max(1,int(ih*s))
                    cg_s=pygame.transform.smoothscale(cg,(nw,nh))
                    x=rx+(pw-nw)//2
                    y=ry+18+(max_h-nh)//2
                    surf.blit(cg_s,(x,y))
            except: pass
            # 底部信息分两行，避免文字重叠
            info_y1=ry+ph-54
            info_y2=ry+ph-30
            tg=font_small.render(display_title,True,INK); surf.blit(tg,(rx+26,info_y1))
            cm=font_small.render(comment,True,(100,80,60))
            surf.blit(cm,cm.get_rect(centerx=SCREEN_WIDTH//2,y=info_y2))
        pn=font_small.render(f'{self.page+1} / {self._max()}',True,(140,120,100))
        surf.blit(pn,pn.get_rect(center=(SCREEN_WIDTH//2,ry+ph+18)))
        if self.page>0: pygame.draw.polygon(surf,PURPLE_LIGHT,[(rx-30,SCREEN_HEIGHT//2),(rx-10,SCREEN_HEIGHT//2-14),(rx-10,SCREEN_HEIGHT//2+14)])
        if self.page<self._max()-1: pygame.draw.polygon(surf,PURPLE_LIGHT,[(rx+pw+30,SCREEN_HEIGHT//2),(rx+pw+10,SCREEN_HEIGHT//2-14),(rx+pw+10,SCREEN_HEIGHT//2+14)])
        hint=font_small.render('ESC 返回菜单  ←→ 翻页',True,(200,180,220))
        surf.blit(hint,hint.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-18)))

def draw_dialogue_box(surf,speaker,displayed,style='dialogue',finished=False,indicator=None):
    box=pygame.Surface((DLG_RECT.w,DLG_RECT.h),pygame.SRCALPHA)
    base=(245,238,215,210) if style=='dialogue' else (230,225,245,200)
    pygame.draw.rect(box,base,(0,0,DLG_RECT.w,DLG_RECT.h),border_radius=10)
    for ly in range(4,DLG_RECT.h,18): pygame.draw.line(box,(200,188,165,60),(8,ly),(DLG_RECT.w-8,ly),1)
    pygame.draw.rect(box,(160,110,180,200),(0,0,DLG_RECT.w,DLG_RECT.h),2,border_radius=10)
    pygame.draw.rect(box,(140,80,180,160),(0,0,5,DLG_RECT.h),border_radius=4)
    surf.blit(box,DLG_RECT.topleft)
    sy=DLG_RECT.y+DLG_PAD_Y
    if style=='dialogue' and speaker:
        ss=font_speaker.render(speaker,True,(120,50,160))
        sb=pygame.Surface((ss.get_width()+16,ss.get_height()+6),pygame.SRCALPHA)
        pygame.draw.rect(sb,(180,140,220,160),(0,0,sb.get_width(),sb.get_height()),border_radius=6)
        surf.blit(sb,(DLG_RECT.x+DLG_PAD_X-8,sy-3))
        surf.blit(ss,(DLG_RECT.x+DLG_PAD_X,sy))
        sy+=ss.get_height()+DLG_LINE_SP+2
    elif style=='narration':
        pf=font_small.render('— ',True,(120,100,160))
        surf.blit(pf,(DLG_RECT.x+DLG_PAD_X,sy+2))
    tc=INK if style=='dialogue' else (80,60,120)
    for line in wrap_text(displayed,font_dialogue,DLG_RECT.w-DLG_PAD_X*2-10):
        ls=font_dialogue.render(line,True,tc)
        surf.blit(ls,(DLG_RECT.x+DLG_PAD_X+8,sy))
        sy+=ls.get_height()+DLG_LINE_SP
        if sy>DLG_RECT.bottom-12: break
    if finished and indicator:
        oy=int(4*math.sin(pygame.time.get_ticks()/250.0))
        ir=indicator.get_rect(bottomright=(DLG_RECT.right-12,DLG_RECT.bottom-10+oy))
        surf.blit(indicator,ir)

def draw_options(surf,options,sel):
    ow=340; oh=44; gap=8
    th=len(options)*(oh+gap)-gap
    sy=SCREEN_HEIGHT//2-th//2
    for i,opt in enumerate(options):
        oy=sy+i*(oh+gap); is_s=(i==sel)
        bg=pygame.Surface((ow,oh),pygame.SRCALPHA)
        pygame.draw.rect(bg,(140,80,200,210) if is_s else (60,20,90,170),(0,0,ow,oh),border_radius=8)
        bc=(*GOLD,220) if is_s else (*PURPLE_LIGHT,180)
        pygame.draw.rect(bg,bc,(0,0,ow,oh),2,border_radius=8)
        surf.blit(bg,(SCREEN_WIDTH//2-ow//2,oy))
        ts=font_option.render(opt.get('text',''),True,GOLD if is_s else WHITE)
        surf.blit(ts,ts.get_rect(center=(SCREEN_WIDTH//2,oy+oh//2)))

class PlayingState:
    def __init__(self):
        self.idx=0; self.type_idx=0; self.type_done=False; self.last_char_t=0
        self.bg_img=None; self.bg_id=''; self.fade_alpha=0
        self.fading_out=False; self.fading_in=False
        self.next_bg_img=None; self.next_idx=0; self.current_bgm=None
        self.options=[]; self.sel_opt=0; self.showing_opts=False
        try:
            p=asset_manager.get_asset_path('UI_next_indicator')
            self.indicator=pygame.image.load(p).convert_alpha()
        except: self.indicator=None
    def reset(self):
        self.idx=0; self.type_idx=0; self.type_done=False
        self.last_char_t=pygame.time.get_ticks()
        self.fading_out=False; self.fading_in=False; self.fade_alpha=0
        self.showing_opts=False
        entry=dialogues[0] if dialogues else {}
        self.bg_id=entry.get('background','scene_old_house')
        self.bg_img=load_bg(self.bg_id)
        collect_cg_by_index(0,self.bg_id,'第一章')
        self._start_bgm(entry.get('bgm'))
        sfx=entry.get('sfx')
        if sfx: play_sfx(sfx)
    def _start_bgm(self,bgm_id):
        if bgm_id and bgm_id!=self.current_bgm:
            try:
                p=asset_manager.get_asset_path(bgm_id)
                if os.path.exists(p): pygame.mixer.music.load(p); pygame.mixer.music.play(-1); self.current_bgm=bgm_id
            except: pass
    def _advance(self):
        global current_state
        if self.idx<len(dialogues)-1:
            ni=self.idx+1; entry=dialogues[ni]
            nb=entry.get('background',self.bg_id)
            if nb!=self.bg_id:
                self.fading_out=True; self.next_bg_img=load_bg(nb)
                self.bg_id=nb; self.next_idx=ni
            else:
                self.idx=ni; self.type_idx=0; self.type_done=False
                self.last_char_t=pygame.time.get_ticks()
                collect_cg_by_index(self.idx,nb,'第一章')
                sfx=entry.get('sfx')
                if sfx: play_sfx(sfx)
                self._start_bgm(entry.get('bgm'))
        else:
            pygame.mixer.music.stop(); credits_state.enter(); current_state=STATE_CREDITS
    def handle_event(self,event):
        global current_state
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE: pygame.mixer.music.stop(); current_state=STATE_MENU; menu_state.enter(); return
            if self.showing_opts:
                if event.key==pygame.K_UP: self.sel_opt=max(0,self.sel_opt-1)
                elif event.key==pygame.K_DOWN: self.sel_opt=min(len(self.options)-1,self.sel_opt+1)
                elif event.key in (pygame.K_RETURN,pygame.K_SPACE): trigger_particles(); self.showing_opts=False; self._advance()
                return
            if event.key in (pygame.K_SPACE,pygame.K_RETURN) and not self.fading_out and not self.fading_in:
                if not self.type_done: self.type_idx=len(dialogues[self.idx]['text']); self.type_done=True
                else: self._advance()
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and not self.fading_out and not self.fading_in:
            if not self.type_done: self.type_idx=len(dialogues[self.idx]['text']); self.type_done=True
            else: self._advance()
    def update(self,dt):
        if not self.type_done and not self.fading_out and not self.fading_in:
            now=pygame.time.get_ticks()
            if now-self.last_char_t>TYPE_DELAY:
                self.type_idx+=1; self.last_char_t=now
                if self.type_idx>=len(dialogues[self.idx]['text']): self.type_idx=len(dialogues[self.idx]['text']); self.type_done=True
        if self.fading_out:
            self.fade_alpha=min(255,self.fade_alpha+8)
            if self.fade_alpha>=255:
                self.fading_out=False; self.fading_in=True; self.bg_img=self.next_bg_img
                self.idx=self.next_idx; self.type_idx=0; self.type_done=False
                self.last_char_t=pygame.time.get_ticks()
                entry=dialogues[self.idx]; collect_cg_by_index(self.idx,self.bg_id,'第一章')
                sfx=entry.get('sfx')
                if sfx: play_sfx(sfx)
                self._start_bgm(entry.get('bgm'))
        elif self.fading_in:
            self.fade_alpha=max(0,self.fade_alpha-8)
            if self.fade_alpha<=0: self.fading_in=False
    def draw(self,surf):
        if self.bg_img: surf.blit(self.bg_img,(0,0))
        else: surf.fill(PURPLE_DEEP)
        if self.fading_out or self.fading_in:
            fs=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
            fs.fill((0,0,0,self.fade_alpha)); surf.blit(fs,(0,0))
        draw_particles(surf)
        if not self.fading_out and not self.fading_in and self.idx<len(dialogues):
            entry=dialogues[self.idx]
            speaker=entry.get('speaker','')
            text=entry.get('text','')
            style='narration' if speaker in ('','旁白') else 'dialogue'
            draw_dialogue_box(surf,speaker,text[:self.type_idx],style,self.type_done,self.indicator)
            if self.showing_opts: draw_options(surf,self.options,self.sel_opt)
        hint=font_small.render('Space/Click 推进   ESC 菜单',True,(200,200,220))
        surf.blit(hint,hint.get_rect(topright=(SCREEN_WIDTH-10,8)))

class CreditsState:
    def __init__(self): self.scroll=0.0; self.speed=50.0; self.finished=False; self._t=0.0
    def enter(self): self.scroll=0.0; self.finished=False; self._t=0.0
    def handle_event(self,event):
        global current_state
        if event.type==pygame.KEYDOWN and (self.finished or event.key==pygame.K_ESCAPE):
            current_state=STATE_MENU; menu_state.enter()
    def update(self,dt):
        self._t+=dt; self.scroll+=self.speed*dt
        if self.scroll>len(CREDITS_LINES)*34+SCREEN_HEIGHT: self.finished=True
    def draw(self,surf):
        draw_dusk_sky(surf,self._t)
        dim=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
        dim.fill((0,0,0,120)); surf.blit(dim,(0,0))
        y=SCREEN_HEIGHT-self.scroll
        for line in CREDITS_LINES:
            if -40<y<SCREEN_HEIGHT+40:
                ts=font_sketch.render(line,True,PURPLE_PALE)
                surf.blit(ts,ts.get_rect(center=(SCREEN_WIDTH//2,int(y))))
            y+=34
        if self.finished:
            h=font_small.render('ESC 返回菜单',True,(200,180,220))
            surf.blit(h,h.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-40)))

menu_state=MenuState()
sketchbook_state=SketchbookState()
playing_state=PlayingState()
credits_state=CreditsState()
menu_state.enter()

running=True
while running:
    dt=clock.tick(FPS)/1000.0
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: pygame.display.toggle_fullscreen()
        if current_state==STATE_MENU: menu_state.handle_event(event)
        elif current_state==STATE_PLAYING: playing_state.handle_event(event)
        elif current_state==STATE_SKETCHBOOK: sketchbook_state.handle_event(event)
        elif current_state==STATE_CREDITS: credits_state.handle_event(event)
    update_particles(dt)
    if current_state==STATE_MENU: menu_state.update(dt)
    elif current_state==STATE_PLAYING: playing_state.update(dt)
    elif current_state==STATE_SKETCHBOOK: sketchbook_state.update(dt)
    elif current_state==STATE_CREDITS: credits_state.update(dt)
    screen.fill(BLACK)
    if current_state==STATE_MENU: menu_state.draw(screen)
    elif current_state==STATE_PLAYING: playing_state.draw(screen)
    elif current_state==STATE_SKETCHBOOK: sketchbook_state.draw(screen)
    elif current_state==STATE_CREDITS: credits_state.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
