"""
Integration fix for ui_app.py to add the enhanced features properly.
This replaces the previous automated integration attempt.
"""

integration_code = '''
        # Enhanced UI features (Fixed Integration)
        try:
            from pf.ui_enhanced import add_theme_controls, remove_open_button
            from pf.ui_enhanced_fixes import wire_project_theme_persistence, add_dynamic_scenario_tooltip
            
            # Add enhanced controls
            add_theme_controls(self)
            remove_open_button(self)
            
            # Add fixes for project theme persistence and dynamic tooltips
            wire_project_theme_persistence(self)
            add_dynamic_scenario_tooltip(self)
            
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
                    self.theme_color_var.trace_remove('write', self.theme_color_var.trace_info()[0][1])
                except:
                    pass
                self.theme_color_var.trace_add('write', update_theme_project_specific)
            
        except Exception as e:
            print(f"Enhanced UI integration failed: {e}")
'''

print("Integration code ready for manual application:")
print("Add this code block at the end of your App.__init__ method in pf/ui_app.py")
print("Replace the existing enhanced UI features block with this:")
print(integration_code)
