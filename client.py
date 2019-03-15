#!/usr/bin/env python3

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

try:
    
    from include import HydrusPy2To3
    
    import wx
    
    HydrusPy2To3.do_2to3_test( wx_error_display_callable = wx.SafeShowMessage )
    
    from include import HydrusExceptions
    from include import HydrusConstants as HC
    from include import HydrusData
    from include import HydrusPaths
    
    import os
    import sys
    import time
    
    from include import ClientController
    import threading
    from include import HydrusGlobals as HG
    from include import HydrusLogger
    import traceback
    
    try:
        
        from twisted.internet import reactor
        
    except:
        
        HG.twisted_is_broke = True
        
    
    #
    
    import argparse
    
    argparser = argparse.ArgumentParser( description = 'hydrus network client (console)' )
    
    argparser.add_argument( '-d', '--db_dir', help = 'set an external db location' )
    argparser.add_argument( '--no_daemons', action='store_true', help = 'run without background daemons' )
    argparser.add_argument( '--no_wal', action='store_true', help = 'run without WAL db journalling' )
    argparser.add_argument( '--no_db_temp_files', action='store_true', help = 'run the db entirely in memory' )
    
    result = argparser.parse_args()
    
    if result.db_dir is None:
        
        db_dir = HC.DEFAULT_DB_DIR
        
        if not HydrusPaths.DirectoryIsWritable( db_dir ) or HC.RUNNING_FROM_OSX_APP:
            
            db_dir = HC.USERPATH_DB_DIR
            
        
    else:
        
        db_dir = result.db_dir
        
    
    db_dir = HydrusPaths.ConvertPortablePathToAbsPath( db_dir, HC.BASE_DIR )
    
    try:
        
        HydrusPaths.MakeSureDirectoryExists( db_dir )
        
    except:
        
        raise Exception( 'Could not ensure db path ' + db_dir + ' exists! Check the location is correct and that you have permission to write to it!' )
        
    
    no_daemons = result.no_daemons
    no_wal = result.no_wal
    HG.no_db_temp_files = result.no_db_temp_files
    
    #
    
    with HydrusLogger.HydrusLogger( db_dir, 'client' ) as logger:
        
        try:
            
            HydrusData.Print( 'hydrus client started' )
            
            if not HG.twisted_is_broke:
                
                threading.Thread( target = reactor.run, name = 'twisted', kwargs = { 'installSignalHandlers' : 0 } ).start()
                
            
            controller = ClientController.Controller( db_dir, no_daemons, no_wal )
            
            controller.Run()
            
        except:
            
            HydrusData.Print( 'hydrus client failed' )
            
            HydrusData.Print( traceback.format_exc() )
            
        finally:
            
            HG.view_shutdown = True
            HG.model_shutdown = True
            
            try:
                
                controller.pubimmediate( 'wake_daemons' )
                
            except:
                
                HydrusData.Print( traceback.format_exc() )
                
            
            reactor.callFromThread( reactor.stop )
            
            HydrusData.Print( 'hydrus client shut down' )
            
        
    
    HG.shutdown_complete = True
    
    if HG.restart:
        
        HydrusData.RestartProcess()
        
    
except Exception as e:
    
    import traceback
    import os
    
    print( traceback.format_exc() )
    
    if 'db_dir' in locals() and os.path.exists( db_dir ):
        
        dest_path = os.path.join( db_dir, 'crash.log' )
        
        with open( dest_path, 'w', encoding = 'utf-8' ) as f:
            
            f.write( traceback.format_exc() )
            
        
        print( 'Critical error occurred! Details written to crash.log!' )
        
    
