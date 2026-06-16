echo "Creating minimal CCAST_.CFG (needed for vcdb)"
echo "C_COMPILE_CMD: tricore-c++" > CCAST_.CFG

echo "Running vcdb get commands"
%VECTORCAST_DIR%\vcdb --db=vcshell.db getallcmdlines --all > commands.txt

echo "Add include paths for source files that are not included already"


echo "Importing filtered commands into new database"
REM %VECTORCAST_DIR%\vcshell --db=vcshell_new.db --inputcmds=commands_filtered.txt putcommand