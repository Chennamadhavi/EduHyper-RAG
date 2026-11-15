import React from 'react';
import { Settings, Save } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Badge from '../../components/common/Badge';

export const TeacherSettingsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Teacher Settings"
        description="Configure pedagogical preferences, LLM verification thresholds, and profile defaults."
        breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Settings' }]}
        badge={<Badge variant="default">Preferences</Badge>}
        actions={
          <Button size="sm" leftIcon={<Save className="w-4 h-4" />}>
            Save Preferences
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>AI Verification Thresholds</CardTitle>
          <CardDescription>
            Configure LangGraph verification sensitivity and minimum hypergraph node confidence.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Verification Strictness"
            defaultValue="High (Threshold: 0.85)"
            disabled
            helperText="Custom verification parameters will be configurable in subsequent steps."
          />
          <Input
            label="Maximum Agentic Retrieval Loops"
            defaultValue="2 iterations"
            disabled
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherSettingsPage;
