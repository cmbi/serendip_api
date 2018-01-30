Processors 24
	
# Do not wait for input on error
OnError Exit

#--Prepare scene------------------------------------------------------------------------------------------------------	
Clear
Colbg white
Fog 0
Hud Off

#--Load_PDB------------------------------------------------------------------------------------------------------
LoadPDB (pdbid),Download=Yes
CleanAll
DelAtom Element H
DelWaterAll
Style Backbone=Ribbon, Sidechain=Off
StickRadius 69%
DelObj !1

DelMol !(chain)

LogAs ProteinSequence.txt
Sequence

Exit
