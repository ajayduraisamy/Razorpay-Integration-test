# # import pygame
# # import razorpay
# # import qrcode
# # import os
# # import time
# # from dotenv import load_dotenv

# # # ---------------- ENV ----------------
# # load_dotenv()
# # RAZORPAY_API_KEY = os.getenv("RAZORPAY_API_KEY")
# # RAZORPAY_SECRET_KEY = os.getenv("RAZORPAY_SECRET_KEY")

# # client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))

# # AMOUNT_RS = 1

# # payment_link_id = None
# # payment_id = None
# # payment_state = "pending"
# # failure_reason = None
# # payment_created_time = time.time()

# # # ---------------- QR GENERATION ----------------
# # def generate_qr_once():
# #     global payment_link_id, payment_created_time

# #     payment = client.payment_link.create({
# #         "amount": AMOUNT_RS * 100,
# #         "currency": "INR",
# #         "accept_partial": False,
# #         "description": "ArkaShine – Sustainable Agri Tech",
# #     })

# #     payment_link_id = payment["id"]
# #     payment_created_time = time.time()

# #     qr = qrcode.make(payment["short_url"])
# #     qr.save("qr.png")

# # # ---------------- PAYMENT CHECK ----------------
# # def check_payment_status():
# #     link = client.payment_link.fetch(payment_link_id)
# #     status = link["status"]

# #     # SUCCESS
# #     if status == "paid":
# #         pid = link["payments"][0]["payment_id"]
# #         return "success", pid

# #     # REAL FAILURE
# #     if status in ["expired", "cancelled"]:
# #         return "failed", status

# #     # USER CANCELLED UPI (handled by timeout)
# #     if status == "attempted":
# #         if time.time() - payment_created_time > 25:
# #             return "failed", "cancelled"
# #         return "pending", None

# #     return "pending", None


# # generate_qr_once()

# # # ---------------- PYGAME UI ----------------
# # pygame.init()
# # WIDTH, HEIGHT = 520, 720
# # screen = pygame.display.set_mode((WIDTH, HEIGHT))
# # pygame.display.set_caption("ArkaShine | Payments")

# # font = pygame.font.SysFont("Segoe UI", 22)
# # title_font = pygame.font.SysFont("Segoe UI", 36, bold=True)
# # amount_font = pygame.font.SysFont("Segoe UI", 42, bold=True)
# # small = pygame.font.SysFont("Segoe UI", 16)

# # WHITE = (255, 255, 255)
# # BG = (18, 22, 30)
# # CARD = (30, 35, 45)
# # GRAY = (170, 170, 170)
# # GREEN = (0, 255, 140)
# # RED = (255, 80, 80)

# # qr_img = pygame.image.load("qr.png")
# # qr_img = pygame.transform.scale(qr_img, (300, 300))

# # # ---------------- SCREENS ----------------
# # def success_screen(pid):
# #     screen.fill(BG)
# #     screen.blit(title_font.render("Payment Successful", True, GREEN), (90, 260))
# #     screen.blit(font.render("Payment ID", True, GRAY), (210, 330))
# #     screen.blit(small.render(pid, True, WHITE), (80, 360))

# # def failed_screen(reason):
# #     screen.fill(BG)
# #     screen.blit(title_font.render("Payment Cancelled", True, RED), (90, 260))
# #     screen.blit(font.render("User cancelled payment", True, GRAY), (130, 320))
# #     screen.blit(small.render("Close app and scan again", True, WHITE), (150, 360))

# # # ---------------- MAIN LOOP ----------------
# # running = True
# # last_check = time.time()

# # while running:
# #     screen.fill(BG)

# #     if payment_state == "pending":
# #         screen.blit(title_font.render("ArkaShine", True, WHITE), (160, 30))
# #         screen.blit(small.render("Deep Tech for Sustainable Agriculture", True, GRAY), (95, 75))

# #         pygame.draw.rect(screen, CARD, (60, 120, 400, 520), border_radius=18)

# #         screen.blit(font.render("Pay Amount", True, GRAY), (200, 150))
# #         screen.blit(amount_font.render(f"₹ {AMOUNT_RS}", True, WHITE), (205, 180))

# #         screen.blit(qr_img, (110, 300))
# #         screen.blit(small.render("Scan from another device to pay", True, GRAY), (145, 655))

# #         if time.time() - last_check > 3:
# #             state, data = check_payment_status()
# #             last_check = time.time()

# #             if state == "success":
# #                 payment_state = "success"
# #                 payment_id = data

# #             elif state == "failed":
# #                 payment_state = "failed"
# #                 failure_reason = data

# #     elif payment_state == "success":
# #         success_screen(payment_id)

# #     elif payment_state == "failed":
# #         failed_screen(failure_reason)

# #     for event in pygame.event.get():
# #         if event.type == pygame.QUIT:
# #             running = False

# #     pygame.display.update()

# # pygame.quit()



# import pygame
# import razorpay
# import qrcode
# import os
# import time
# import json
# from dotenv import load_dotenv

# # ================= ENV =================
# load_dotenv()

# RAZORPAY_API_KEY = os.getenv("RAZORPAY_API_KEY")
# RAZORPAY_SECRET_KEY = os.getenv("RAZORPAY_SECRET_KEY")

# client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_SECRET_KEY))

# # ================= CONFIG =================
# AMOUNT_RS = 1
# STATUS_FILE = "payment_status.json"

# payment_state = "pending"
# payment_id = None
# failure_reason = None

# # ================= CLEAN OLD STATUS =================
# if os.path.exists(STATUS_FILE):
#     os.remove(STATUS_FILE)

# # ================= QR GENERATION =================
# def generate_qr():
#     payment = client.payment_link.create({
#         "amount": AMOUNT_RS * 100,
#         "currency": "INR",
#         "accept_partial": False,
#         "description": "ArkaShine – Sustainable Agri Tech",
#     })

#     qr = qrcode.make(payment["short_url"])
#     qr.save("qr.png")

# # ================= WEBHOOK STATUS READER =================
# def read_webhook_status():
#     if not os.path.exists(STATUS_FILE):
#         return "pending", None

#     with open(STATUS_FILE, "r") as f:
#         data = json.load(f)

#     return data.get("state"), data

# # ================= UI =================
# pygame.init()
# WIDTH, HEIGHT = 520, 720
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("ArkaShine | Payments")

# font = pygame.font.SysFont("Segoe UI", 22)
# title_font = pygame.font.SysFont("Segoe UI", 36, bold=True)
# amount_font = pygame.font.SysFont("Segoe UI", 42, bold=True)
# small = pygame.font.SysFont("Segoe UI", 16)

# WHITE = (255, 255, 255)
# BG = (18, 22, 30)
# CARD = (30, 35, 45)
# GRAY = (170, 170, 170)
# GREEN = (0, 255, 140)
# RED = (255, 80, 80)

# generate_qr()

# qr_img = pygame.image.load("qr.png")
# qr_img = pygame.transform.scale(qr_img, (300, 300))

# # ================= SCREENS =================
# def success_screen(pid):
#     screen.fill(BG)
#     screen.blit(title_font.render("Payment Successful", True, GREEN), (90, 260))
#     screen.blit(font.render("Payment ID", True, GRAY), (210, 330))
#     screen.blit(small.render(pid, True, WHITE), (80, 360))

# def failed_screen(reason):
#     screen.fill(BG)
#     screen.blit(title_font.render("Payment Cancelled", True, RED), (90, 260))
#     screen.blit(font.render("Payment failed or cancelled", True, GRAY), (115, 320))
#     screen.blit(small.render("Close app and scan again", True, WHITE), (150, 360))

# # ================= MAIN LOOP =================
# running = True
# last_check = time.time()

# while running:
#     screen.fill(BG)

#     if payment_state == "pending":
#         screen.blit(title_font.render("ArkaShine", True, WHITE), (160, 30))
#         screen.blit(small.render("Deep Tech for Sustainable Agriculture", True, GRAY), (95, 75))

#         pygame.draw.rect(screen, CARD, (60, 120, 400, 520), border_radius=18)

#         screen.blit(font.render("Pay Amount", True, GRAY), (200, 150))
#         screen.blit(amount_font.render(f"₹ {AMOUNT_RS}", True, WHITE), (205, 180))

#         screen.blit(qr_img, (110, 300))
#         screen.blit(small.render("Scan from another device to pay", True, GRAY), (145, 655))

#         # 🔥 WEBHOOK SYNC (every 2 sec)
#         if time.time() - last_check > 2:
#             state, data = read_webhook_status()
#             last_check = time.time()

#             if state == "success":
#                 payment_state = "success"
#                 payment_id = data["payment_id"]

#             elif state == "failed":
#                 payment_state = "failed"
#                 failure_reason = data.get("reason", "Cancelled")

#     elif payment_state == "success":
#         success_screen(payment_id)

#     elif payment_state == "failed":
#         failed_screen(failure_reason)

#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     pygame.display.update()

# pygame.quit()
