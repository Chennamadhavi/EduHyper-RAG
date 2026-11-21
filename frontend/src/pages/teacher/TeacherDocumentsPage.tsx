import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertCircle,
  Network,
  Layers,
  Database,
  Loader2,
  Calendar,
  FileCheck,
} from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import documentService from '../../services/documentService';
import courseService from '../../services/courseService';
import { DocumentItem, DocumentUploadResult } from '../../types/document';
import { Course } from '../../types/course';

export const TeacherDocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Upload Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<DocumentUploadResult | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [docsData, coursesData] = await Promise.all([
        documentService.listDocuments(),
        courseService.listCourses(),
      ]);
      setDocuments(docsData);
      setCourses(coursesData);
      if (coursesData.length > 0 && !selectedCourseId) {
        setSelectedCourseId(coursesData[0].id.toString());
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
      setUploadSuccess(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError(null);
    setUploadSuccess(null);

    if (!selectedCourseId) {
      setUploadError('Please select a target course.');
      return;
    }

    if (!selectedFile) {
      setUploadError('Please select a PDF or text file to upload.');
      return;
    }

    setUploading(true);
    try {
      const result = await documentService.uploadDocument(
        parseInt(selectedCourseId, 10),
        selectedFile
      );
      setUploadSuccess(result);
      setSelectedFile(null);
      await fetchData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Ingestion failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Educational Documents"
        description="Upload textbooks and research papers to invoke the Phase 1-4 preprocessing, hypergraph, and vector pipeline."
        breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Documents' }]}
        badge={<Badge variant="purple">Phase 1-4 Ingestion Pipeline</Badge>}
        actions={
          <Button
            size="sm"
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => {
              setIsModalOpen(true);
              setUploadSuccess(null);
              setUploadError(null);
            }}
          >
            Upload Document
          </Button>
        }
      />

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState message="Fetching ingested documents..." size="lg" />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-8 h-8 text-purple-600" />}
          title="No Documents Uploaded"
          description="Upload textbook PDFs or lecture notes to trigger automatic chunking, concept extraction, and hypergraph construction."
          action={
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Upload className="w-4 h-4" />}
              onClick={() => setIsModalOpen(true)}
            >
              Upload First Document
            </Button>
          }
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3.5">Document Name</th>
                  <th className="px-6 py-3.5">Course</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-center">Chunks</th>
                  <th className="px-6 py-3.5 text-center">Concepts</th>
                  <th className="px-6 py-3.5 text-center">Hyperedges</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900">{doc.filename}</div>
                          <div className="text-[11px] text-slate-400 font-mono">{doc.doc_id}</div>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      {doc.course_code ? (
                        <Badge variant="purple" size="sm">
                          {doc.course_code}
                        </Badge>
                      ) : (
                        <span className="text-xs text-slate-400">Course #{doc.course_id}</span>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <Badge
                        variant={
                          doc.status === 'READY'
                            ? 'success'
                            : doc.status === 'PROCESSING'
                            ? 'primary'
                            : 'danger'
                        }
                        size="sm"
                      >
                        {doc.status}
                      </Badge>
                    </td>

                    <td className="px-6 py-4 text-center font-medium text-slate-700">
                      <span className="inline-flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        {doc.num_chunks}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-center font-medium text-slate-700">
                      <span className="inline-flex items-center gap-1">
                        <FileCheck className="w-3.5 h-3.5 text-blue-500" />
                        {doc.num_concepts}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-center font-medium text-slate-700">
                      <span className="inline-flex items-center gap-1">
                        <Network className="w-3.5 h-3.5 text-purple-500" />
                        {doc.num_hyperedges}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">
                      {doc.created_at ? doc.created_at.split(' ')[0] : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Upload Document Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => !uploading && setIsModalOpen(false)}
        title="Upload & Ingest Educational Document"
        maxWidth="lg"
      >
        <form onSubmit={handleUpload} className="space-y-4">
          {uploadError && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadSuccess && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-2">
              <div className="flex items-center gap-2 font-semibold text-emerald-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Ingestion Pipeline Completed Successfully</span>
              </div>
              <p className="text-emerald-700">
                Extracted <strong>{uploadSuccess.num_chunks}</strong> semantic chunks,{' '}
                <strong>{uploadSuccess.num_concepts}</strong> concepts, and{' '}
                <strong>{uploadSuccess.num_hyperedges}</strong> hyperedges for{' '}
                <em>{uploadSuccess.filename}</em>.
              </p>
            </div>
          )}

          {/* Target Course Selector */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Assign to Course
            </label>
            {courses.length === 0 ? (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>No Courses Found for Your Instructor Account</span>
                </div>
                <p className="text-amber-700">
                  Documents must be assigned to a course. Please create a course under <strong>My Courses</strong> before uploading files.
                </p>
                <div className="pt-1">
                  <a
                    href="/teacher/courses"
                    className="inline-flex items-center font-semibold text-blue-600 hover:text-blue-800 underline"
                  >
                    Go to Courses &rarr;
                  </a>
                </div>
              </div>
            ) : (
              <select
                value={selectedCourseId}
                onChange={(e) => setSelectedCourseId(e.target.value)}
                disabled={uploading}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="" disabled>-- Select a course --</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id.toString()}>
                    {c.course_code} — {c.title}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* File Picker */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Document File (.pdf, .txt, .md)
            </label>
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-blue-500 transition-colors bg-slate-50/50">
              <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <input
                type="file"
                id="doc-upload-input"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                disabled={uploading}
                className="hidden"
              />
              <label
                htmlFor="doc-upload-input"
                className="cursor-pointer text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                Click to browse
              </label>
              <span className="text-xs text-slate-500 block mt-1">
                {selectedFile ? selectedFile.name : 'PDF, TXT, or Markdown educational files up to 50MB'}
              </span>
            </div>
          </div>

          {/* Ingestion Steps Preview */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1">
            <div className="font-semibold text-slate-700 mb-1">
              Automated Ingestion Pipeline:
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                <span>Phase 1: Dual Chunking</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-600" />
                <span>Phase 2: Concept Extraction</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
                <span>Phase 3: HyperNetX Graph</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Phase 4: ChromaDB Index</span>
              </div>
            </div>
          </div>

          {uploading && (
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-800 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600 shrink-0" />
              <span>Processing document through Phase 1-4 pipelines. Please wait...</span>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsModalOpen(false)}
              disabled={uploading}
            >
              Close
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={uploading}
              disabled={!selectedFile}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              Start Ingestion
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TeacherDocumentsPage;
