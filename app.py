import pygame
import razorpay
import qrcode
import os
import time
import json
from dotenv import load_dotenv

#  ENV 
load_dotenv()

RAZORPAY_API_KEY = os.getenv("RAZORPAY_API_KEY")
RAZORPAY_SECRET_KEY = os.getenv("RAZORPAY_SECRET_KEY")

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))

#  CONFIG 
AMOUNT_RS = 1
STATUS_FILE = "payment_status.json"

payment_state = "pending"
payment_id = None
failure_reason = None

#  DO NOT DELETE STATUS FILE
print("[INFO] Waiting for webhook updates...")

#  QR GENERATION 
def generate_qr():
    payment = client.payment_link.create({
        "amount": AMOUNT_RS * 100,
        "currency": "INR",
        "accept_partial": False,
        "description": "ArkaShine – Sustainable Agri Tech",
    })

    qr = qrcode.make(payment["short_url"])
    qr.save("qr.png")

    print("[INFO] QR Generated:", payment["short_url"])
    return payment["id"]

#  READ WEBHOOK 
def read_webhook_status():
    if not os.path.exists(STATUS_FILE):
        return None, None

    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None, None

        #  pick FINAL state only
        for pid, info in data.items():
            if info.get("state") in ("success", "failed"):
                return info["state"], info

    except Exception as e:
        print("[ERROR] JSON read:", e)

    return None, None

#  PYGAME UI 
pygame.init()
screen = pygame.display.set_mode((520, 720))
pygame.display.set_caption("ArkaShine | Payments")

font = pygame.font.SysFont("Segoe UI", 22)
title_font = pygame.font.SysFont("Segoe UI", 36, bold=True)
amount_font = pygame.font.SysFont("Segoe UI", 42, bold=True)
small = pygame.font.SysFont("Segoe UI", 16)

WHITE = (255, 255, 255)
BG = (18, 22, 30)
CARD = (30, 35, 45)
GRAY = (170, 170, 170)
GREEN = (0, 255, 140)
RED = (255, 80, 80)

#  GENERATE QR 
generate_qr()
qr_img = pygame.transform.scale(pygame.image.load("qr.png"), (300, 300))

#  SCREENS 
def success_screen(pid):
    screen.fill(BG)
    screen.blit(title_font.render("Payment Successful", True, GREEN), (80, 260))
    screen.blit(font.render("Payment ID", True, GRAY), (190, 330))
    screen.blit(small.render(pid, True, WHITE), (100, 360))

def failed_screen(reason):
    screen.fill(BG)
    screen.blit(title_font.render("Payment Failed", True, RED), (100, 260))
    screen.blit(font.render("Reason", True, GRAY), (210, 320))
    screen.blit(small.render(reason, True, WHITE), (80, 350))

#  MAIN LOOP 
running = True
last_check = 0

while running:
    screen.fill(BG)

    if payment_state == "pending":
        screen.blit(title_font.render("ArkaShine", True, WHITE), (160, 30))
        pygame.draw.rect(screen, CARD, (60, 120, 400, 520), border_radius=18)

        screen.blit(font.render("Pay Amount", True, GRAY), (200, 150))
        screen.blit(amount_font.render(f"₹ {AMOUNT_RS}", True, WHITE), (205, 180))

        screen.blit(qr_img, (110, 300))
        screen.blit(small.render("Scan from another device to pay", True, GRAY), (145, 655))

        # Poll webhook
        if time.time() - last_check > 2:
            last_check = time.time()
            state, data = read_webhook_status()
            print("[DEBUG] Poll:", state, data)

            if state == "success":
                payment_state = "success"
                payment_id = data["payment_id"]

            elif state == "failed":
                payment_state = "failed"
                failure_reason = data.get("description", "Payment timeout")

    elif payment_state == "success":
        success_screen(payment_id)

    elif payment_state == "failed":
        failed_screen(failure_reason)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()

pygame.quit()
