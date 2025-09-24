"""
Final UI integration that replaces the debug version.
This should be integrated into ui_app.py to replace the current enhanced UI block.
"""

final_integration_code = '''
        # Enhanced UI features with complete project persistence
        try:
            from pf.ui_enhanced import add_theme_controls, remove_open_button
            from pf.project_persistence import wire_complete_project_persistence
            
            # Add enhanced controls
            add_theme_controls(self)
            remove_open_button(self)
            
            # Wire complete project and theme persistence
            wire_complete_project_persistence(self)
            
            # Update theme color save method to be project-specific
            if hasattr(self, 'theme_color_var'):
                def update_theme_project_specific(*args):
                    color = self.theme_color_var.get().strip()
                    if color.startswith('#') and len(color) == 7:
                        from pf.ui_enhanced_fixes import save_theme_color_to_current_project, apply_theme_immediately
                        if save_theme_color_to_current_project(self, color):
                            apply_theme_immediately(self, color)
                
                # Remove old trace and add new one
                try:
                    traces = self.theme_color_var.trace_info()
                    if traces:
                        self.theme_color_var.trace_remove('write', traces[0][1])
                except:
                    pass
                self.theme_color_var.trace_add('write', update_theme_project_specific)
            
        except Exception as e:
            print(f"Enhanced UI integration failed: {e}")
            import traceback
            traceback.print_exc()
'''

print("Integration code ready:")
print("Replace the 'Enhanced UI features' block in pf/ui_app.py with:")
print(final_integration_code)
