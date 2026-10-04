"""Smoke asset / builder contract example. Replace geometry for the actual request."""
from modeling import material,rounded_box
def build_body(ctx):
 w,d,h=ctx['dimensions'] or (.16,.10,.20)
 mat=material('paint',(.14,.32,.42));rounded_box('CabinetBody',(0,0,h/2),(w,d,h),ctx['asset'],mat)
def add_details(ctx):
 w,d,h=ctx['dimensions'] or (.16,.10,.20)
 rounded_box('Handle',(0,-d/2-.006,h*.6),(w*.3,.012,.008),ctx['asset'],material('brass',(.6,.32,.07)),.002)
def edit(ctx):
 import bpy
 bpy.data.objects['Handle'].location.z+=.005
