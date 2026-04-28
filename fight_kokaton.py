import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: "Bomb"):
        """
        爆発画像を読み込み，位置と表示時間を設定する
        引数 bomb：衝突した爆弾のインスタンス
        """
        img = pg.image.load("fig/explosion.gif")
        # 元の画像と、上下左右にフリップした画像の2つをリストに格納
        self.imgs = [img, pg.transform.flip(img, True, True)]
        self.rct = img.get_rect()
        self.rct.center = bomb.rct.center  # 爆発した爆弾のrct.centerに座標を設定
        self.life = 20  # 表示時間（爆発時間）を設定

    def update(self, screen: pg.Surface):
        """
        爆発時間を減算し，交互に画像を切り替えて描画する
        引数 screen：画面Surface
        """
        self.life -= 1  # 爆発経過時間lifeを1減算
        if self.life > 0:
            # lifeの値に応じて画像を交互に切り替える（チラチラ防止の工夫）
            img_idx = self.life % 2
            screen.blit(self.imgs[img_idx], self.rct)


class Score:
    """
    打ち落とした爆弾の数を表示するスコアに関するクラス
    """
    def __init__(self):
        self.fonto = pg.font.SysFont(None, 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    score = Score()
    beams = []
    exps = []  # Explosionインスタンス用の空リスト
    clock = pg.time.Clock()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))            
        
        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(6, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        
        # 爆弾とビームの衝突判定
        for i, beam in enumerate(beams):
            for j, bomb in enumerate(bombs):
                if beam is not None and bomb is not None:
                    if beam.rct.colliderect(bomb.rct):
                        # 衝突したらExplosionインスタンスを生成し，リストにappend
                        exps.append(Explosion(bomb))
                        beams[i] = None
                        bombs[j] = None
                        score.score += 1
        
        # Noneの除外処理
        beams = [b for b in beams if b is not None]
        bombs = [b for b in bombs if b is not None]
        
        # 画面外に出たビームの削除
        beams = [b for b in beams if check_bound(b.rct) == (True, True)]
        
        # 爆発時間が残っているインスタンスだけにする
        exps = [e for e in exps if e.life > 0]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        for beam in beams:
            beam.update(screen)
        for bomb in bombs:
            bomb.update(screen)
        for exp in exps:  # 爆発の描画
            exp.update(screen)
            
        score.update(screen)
        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()