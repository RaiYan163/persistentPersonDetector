#!/usr/bin/env python3
# start_person_tracker.py - Launcher script for Person Tracker with gesture configuration

"""
Person Tracker Launcher

This script provides two startup options:
1. Configuration GUI first (default) - Configure gesture mappings then start tracking
2. Direct start - Skip configuration and use existing/default settings

Usage:
    python start_person_tracker.py              # Start with configuration GUI
    python start_person_tracker.py --direct     # Start directly with existing config
    python start_person_tracker.py --config     # Open configuration GUI only
"""

import argparse
import sys
import os

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Person Tracker Launcher - Gesture Configuration & Tracking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_person_tracker.py                    # Configure gestures then start
  python start_person_tracker.py --direct           # Start with existing settings
  python start_person_tracker.py --config           # Configuration GUI only
  python start_person_tracker.py --direct --source 1  # Direct start with camera 1
        """
    )
    
    # Startup mode options
    startup_group = parser.add_mutually_exclusive_group()
    startup_group.add_argument(
        "--config", 
        action="store_true",
        help="Open configuration GUI only (don't start tracking)"
    )
    startup_group.add_argument(
        "--direct", 
        action="store_true",
        help="Start tracking directly without configuration GUI"
    )
    
    # Pass-through arguments for main.py
    parser.add_argument("--source", type=str, default="0", 
                       help="Camera index or video file path")
    parser.add_argument("--conf", type=float, default=0.5,
                       help="YOLO confidence threshold")
    parser.add_argument("--sim", type=float, default=0.30,
                       help="ReID similarity threshold")
    parser.add_argument("--gesture_conf", type=float, default=0.50,
                       help="Gesture detection confidence")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device for ReID model (cpu/cuda)")
    parser.add_argument("--loss_timeout", type=float, default=15.0,
                       help="Seconds before auto-unlock")
    parser.add_argument("--width", type=int, default=1280,
                       help="Display width")
    parser.add_argument("--height", type=int, default=720,
                       help="Display height")
    parser.add_argument("--fullscreen", action="store_true",
                       help="Start in fullscreen mode")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug output")
    
    return parser.parse_args()

def check_configuration_exists():
    """Check if gesture configuration files exist"""
    config_files = ["gesture_config.json", "runtime_gesture_config.json"]
    return any(os.path.exists(f) for f in config_files)

def start_configuration_gui():
    """Start the gesture configuration GUI"""
    print("🎮 Starting Gesture Configuration GUI...")
    print("=" * 50)
    
    try:
        import gesture_config_gui
        gesture_config_gui.main()
        return True
    except ImportError as e:
        print(f"❌ Error: Could not import gesture_config_gui: {e}")
        print("Make sure gesture_config_gui.py is in the same directory.")
        return False
    except Exception as e:
        print(f"❌ Error starting configuration GUI: {e}")
        return False

def start_main_application(args):
    """Start the main Person Tracker application"""
    print("🚀 Starting Person Tracker...")
    print("=" * 50)
    
    try:
        # Prepare sys.argv for main.py
        main_args = ['main.py']
        
        if args.source != "0":
            main_args.extend(['--source', str(args.source)])
        if args.conf != 0.5:
            main_args.extend(['--conf', str(args.conf)])
        if args.sim != 0.30:
            main_args.extend(['--sim', str(args.sim)])
        if args.gesture_conf != 0.50:
            main_args.extend(['--gesture_conf', str(args.gesture_conf)])
        if args.device != "cpu":
            main_args.extend(['--device', args.device])
        if args.loss_timeout != 15.0:
            main_args.extend(['--loss_timeout', str(args.loss_timeout)])
        if args.width != 1280:
            main_args.extend(['--width', str(args.width)])
        if args.height != 720:
            main_args.extend(['--height', str(args.height)])
        if args.fullscreen:
            main_args.append('--fullscreen')
        if args.debug:
            main_args.append('--debug')
        
        # Set sys.argv for main.py
        original_argv = sys.argv.copy()
        sys.argv = main_args
        
        # Import and run main
        import main
        main.main()
        
        # Restore original sys.argv
        sys.argv = original_argv
        
    except ImportError as e:
        print(f"❌ Error: Could not import main.py: {e}")
        print("Make sure main.py and all dependencies are available.")
        return False
    except Exception as e:
        print(f"❌ Error starting main application: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🎯 Person Tracker - Gesture Configuration & Tracking System")
    print("=" * 60)
    
    args = parse_arguments()
    
    # Handle different startup modes
    if args.config:
        # Configuration GUI only
        print("📋 Opening Gesture Configuration GUI...")
        start_configuration_gui()
        
    elif args.direct:
        # Direct start - skip configuration
        print("⚡ Starting directly with existing configuration...")
        
        if not check_configuration_exists():
            print("⚠️  Warning: No gesture configuration found, using defaults.")
            print("   Consider running with configuration GUI first:")
            print("   python start_person_tracker.py")
            print()
        
        start_main_application(args)
        
    else:
        # Default: Configuration GUI first, then start tracking
        print("📋 Step 1: Configure gesture mappings")
        print("🚀 Step 2: Start person tracking")
        print()
        
        print("Opening Gesture Configuration GUI...")
        print("Configure your gestures and click 'Start Person Tracker' when ready.")
        print()
        
        # Check if configuration already exists
        if check_configuration_exists():
            print("ℹ️  Existing configuration found - you can modify it or use as-is.")
        
        # Start configuration GUI
        # Note: The configuration GUI will handle starting the main app
        start_configuration_gui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
    finally:
        print("\n👋 Thank you for using Person Tracker!")