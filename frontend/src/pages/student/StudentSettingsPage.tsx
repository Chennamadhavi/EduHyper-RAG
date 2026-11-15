import React from 'react';
import { Settings, Save } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Badge from '../../components/common/Badge';

export const StudentSettingsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Student Settings"
        description="Manage your learning preferences, explanation verbosity, and notification options."
        breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'Settings' }]}
        badge={<Badge variant="default">Preferences</Badge>}
        actions={
          <Button size="sm" leftIcon={<Save className="w-4 h-4" />}>
            Save Preferences
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Tutor Preferences</CardTitle>
          <CardDescription>
            Tailor AI explanations to your learning level.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Explanation Depth"
            defaultValue="Standard Educational (Concise with Citations)"
            disabled
            helperText="Custom explanation depths will be enabled in future releases."
          />
          <Input
            label="Language Preference"
            defaultValue="English (Primary)"
            disabled
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentSettingsPage;
