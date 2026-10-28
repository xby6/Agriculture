<template>
  <div class="app-container agri-business-page">
    <AgriPageHeader
      class="analysis-page-header"
      title="农业模型分析任务"
      eyebrow="MODEL ANALYSIS TASKS"
      icon="DataAnalysis"
      description="创建病害图像检测、病情指数预测、遥感长势评估和报告生成任务，统一查看输入数据、运行进度与分析结果。"
    />
    <el-form
      v-show="showSearch"
      ref="queryRef"
      :model="queryParams"
      :inline="true"
      label-width="92px"
      class="analysis-filter-panel"
    >
      <el-form-item label="分析任务名称" prop="name">
        <el-input v-model="queryParams.name" placeholder="请输入分析任务名称" clearable style="width: 240px"
          @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="算法服务" prop="container">
        <el-select v-model="queryParams.container" placeholder="请选择算法服务" clearable style="width: 240px">
          <el-option v-for="container in containers" :key="container.id" :label="container.name"
            :value="container.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="农业模型/算法" prop="algo">
        <el-select v-model="queryParams.algo" placeholder="请选择农业模型/算法" clearable style="width: 240px">
          <el-option v-for="algorithm in algorithms" :key="algorithm.name" :label="algorithm.name"
            :value="algorithm.name" />
        </el-select>
      </el-form-item>
      <el-form-item label="运行状态" prop="state">
        <el-select v-model="queryParams.state" placeholder="请选择运行状态" clearable style="width: 240px">
          <el-option label="全部" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="analysis-toolbar mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['task:task:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate"
          v-hasPermi="['task:task:edit']">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete"
          v-hasPermi="['task:task:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table
      v-loading="loading"
      :data="taskList"
      class="analysis-task-table"
      stripe
      row-key="id"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="任务标识" align="center" prop="id" />
      <el-table-column label="分析任务名称" align="center" prop="name" />
      <el-table-column label="算法服务" align="center" prop="container">
        <template #default="scope">
          <span>{{ getContainerName(scope.row.container) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="农业模型/算法" align="center" prop="algo" />
      <el-table-column label="模型运行参数" align="center" prop="args" width="120">
        <template #default="scope">
          <el-tooltip effect="dark" placement="top">
            <template #content>
              <div style="max-width: 400px; white-space: pre-wrap;">{{ formatArgs(scope.row.args) }}</div>
            </template>
            <el-button link type="primary">查看参数</el-button>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="备注信息" align="center" prop="remark" />
      <el-table-column label="运行状态" align="center" prop="state">
        <template #default="scope">
          <div style="display: flex; align-items: center; justify-content: center;">
            <el-tag :type="getStatusType(scope.row.state, scope.row.result)">
              {{ getStatusText(scope.row.state, scope.row.result) }}
            </el-tag>
            <el-icon v-if="!scope.row.result && (scope.row.state === 'running' || scope.row.state === '')"
              class="is-loading" style="margin-left: 5px;">
              <Loading />
            </el-icon>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="分析结果" align="center" prop="result" width="120">
        <template #default="scope">
          <el-button v-if="scope.row.result" link type="primary"
            @click="openResultFolder(scope.row.result, scope.row.name)">
            <el-icon>
              <FolderOpened />
            </el-icon>
            查看结果
          </el-button>
          <el-tag v-else-if="!scope.row.result && (scope.row.state === 'running' || scope.row.state === '')"
            type="warning">执行中...</el-tag>
          <el-tag v-else-if="scope.row.state === 'pending'" type="info">等待执行</el-tag>
          <el-tag v-else-if="scope.row.state === 'failed'" type="danger">执行失败</el-tag>
          <span v-else-if="!scope.row.result && scope.row.state === 'completed'" class="no-result">无结果</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="任务创建时间" align="center" prop="init_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.init_time, '{y}-{m}-{d} {h}:{i}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="任务结束时间" align="center" prop="end_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.end_time, '{y}-{m}-{d} {h}:{i}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="VideoPlay" @click="handleExecute(scope.row)"
            :disabled="scope.row.state === 'running'" v-hasPermi="['task:task:execute']">执行</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)"
            v-hasPermi="['task:task:edit']">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)"
            v-hasPermi="['task:task:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      class="analysis-main-pagination"
      :total="total"
      @pagination="getList"
    />

    <!-- 添加或修改农业分析任务对话框 -->
    <el-dialog
      v-model="open"
      :title="title"
      width="880px"
      append-to-body
      class="analysis-task-dialog"
    >
      <el-form ref="taskRef" :model="form" :rules="rules" label-width="100px">
        <el-steps :active="currentStep" align-center style="margin-bottom: 20px;">
          <el-step title="选择农业模型服务" />
          <el-step title="选择农业模型" />
          <el-step title="选择文件" />
          <el-step title="配置参数" />
        </el-steps>

        <!-- 第一步：选择农业模型服务 -->
        <div v-if="currentStep === 0">
          <el-form-item label="算法服务" prop="container">
            <el-select v-model="form.container" placeholder="请选择算法服务" style="width: 100%" @change="onContainerChange"
              :loading="containerLoading">
              <el-option v-for="container in containers" :key="container.id" :label="container.name"
                :value="container.id" />
            </el-select>
          </el-form-item>
          <div class="step-actions">
            <el-button type="primary" @click="currentStep = 1" :disabled="!form.container">下一步</el-button>
          </div>
        </div>

        <!-- 第二步：选择农业模型 -->
        <div v-if="currentStep === 1">
          <el-form-item label="农业模型/算法" prop="algo">
            <el-select v-model="form.algo" placeholder="请选择农业模型/算法" style="width: 100%" :disabled="!form.container"
              :loading="algorithmLoading" @change="onAlgorithmSelect">
              <el-option v-for="algorithm in containerAlgorithms[form.container] || []" :key="algorithm.name"
                :label="algorithm.name" :value="algorithm.name" />
            </el-select>
          </el-form-item>
          <div class="step-actions">
            <el-button @click="currentStep = 0">上一步</el-button>
            <el-button type="primary" @click="currentStep = 2" :disabled="!form.algo">下一步</el-button>
          </div>
        </div>

        <!-- 第三步：选择文件 -->
        <div v-if="currentStep === 2">
          <el-form-item label="选择农业输入数据">
            <div class="file-selection-container">
              <div class="file-selection-header">
                <span class="file-selection-title">已选文件</span>
                <el-button type="primary" @click="openFileSelectionDialog">
                  <el-icon>
                    <Plus />
                  </el-icon>选择文件
                </el-button>
              </div>

              <!-- 已选文件列表 -->
              <div v-if="selectedFiles.length > 0" class="selected-files-list">
                <div v-for="file in selectedFiles" :key="file.id" class="selected-file-item">
                  <div class="file-info">
                    <el-icon>
                      <Document />
                    </el-icon>
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">({{ formatFileSize(file.size) }})</span>
                    <el-tag v-if="file.folderPath" size="small" type="info">
                      {{ file.folderPath }}
                    </el-tag>
                  </div>
                  <el-button type="danger" link @click="removeSelectedFile(file.id)">
                    <el-icon>
                      <Delete />
                    </el-icon>
                  </el-button>
                </div>
              </div>
              <div v-else class="no-files-tip">
                <el-empty description="暂未选择文件" :image-size="80" />
              </div>

              <div class="selected-count">
                已选择 {{ selectedFiles.length }} 个文件
              </div>
            </div>
          </el-form-item>

          <div class="step-actions">
            <el-button @click="currentStep = 1">上一步</el-button>
            <el-button type="primary" @click="currentStep = 3" :disabled="selectedFiles.length === 0">下一步</el-button>
          </div>
        </div>

        <!-- 第四步：配置参数 -->
        <div v-if="currentStep === 3">
          <el-form-item label="分析任务名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入分析任务名称" />
          </el-form-item>

          <el-form-item label="备注信息" prop="remark">
            <el-input v-model="form.remark" placeholder="请输入备注信息" type="textarea" :rows="3" />
          </el-form-item>

          <el-form-item label="模型运行参数配置">
            <div class="param-container">
              <div class="param-header">
                <span class="param-title">参数配置</span>
                <el-button type="primary" link @click="addParameter">
                  <el-icon>
                    <Plus />
                  </el-icon>添加参数
                </el-button>
              </div>

              <!-- 显示算法参数说明 -->
              <div v-if="algorithmParams.length > 0" class="algorithm-params-info">
                <h4>算法参数说明：</h4>
                <div v-for="param in algorithmParams" :key="param.name" class="param-info-item">
                  <span class="param-name">{{ param.name }}:</span>
                  <span class="param-intro">{{ param.intro }}</span>
                  <span v-if="param.default && param.default !== '默认值'" class="param-default">(默认值: {{ param.default
                    }})</span>
                </div>
              </div>

              <div v-else class="algorithm-params-info">
                <h4>算法参数说明：</h4>
                <p class="no-params-tip">该算法没有预定义的参数配置，请根据需要手动添加参数。</p>
              </div>

              <!-- 参数列表 -->
              <div v-for="(param, index) in form.params" :key="index" class="param-item">
                <div class="param-item-header">
                  <span>参数 {{ index + 1 }}</span>
                  <el-button type="danger" link @click="removeParameter(index)">
                    <el-icon>
                      <Delete />
                    </el-icon>删除
                  </el-button>
                </div>

                <el-row :gutter="10">
                  <el-col :span="6">
                    <el-form-item label="参数名" :prop="`params.${index}.name`"
                      :rules="{ required: true, message: '参数名不能为空', trigger: 'blur' }">
                      <el-input v-model="param.name" placeholder="参数名称" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="6">
                    <el-form-item label="参数类型">
                      <el-select v-model="param.type" placeholder="请选择" @change="onParamTypeChange(param)">
                        <el-option label="字符串" value="string" />
                        <el-option label="整数" value="int" />
                        <el-option label="浮点数" value="float" />
                        <el-option label="布尔值" value="bool" />
                        <el-option label="文件" value="file" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="10">
                    <el-form-item label="参数值" :prop="`params.${index}.value`" :rules="getParamRules(param)">
                      <div v-if="param.type === 'file'" class="file-param-input">
                        <el-input v-model="param.value" placeholder="请选择文件" readonly />
                        <el-button type="primary" @click="openFileParamSelection(param)" style="margin-left: 10px;">
                          选择文件
                        </el-button>
                      </div>
                      <el-input v-else v-model="param.value" :placeholder="getParamPlaceholder(param.type)" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <div v-if="param.type === 'file' && param.value" class="file-param-info">
                  <el-tag type="success" size="small">
                    <el-icon>
                      <Document />
                    </el-icon>
                    {{ getFileNameById(param.value) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-form-item>

          <div class="step-actions">
            <el-button @click="currentStep = 2">上一步</el-button>
            <el-button type="primary" @click="submitForm">提交</el-button>
          </div>
        </div>
      </el-form>
    </el-dialog>


    <!-- 文件选择对话框 - 树状结构 -->
    <el-dialog
      v-model="fileSelectionDialogVisible"
      title="选择文件"
      width="1080px"
      append-to-body
      class="analysis-file-dialog"
    >
      <div class="file-selection-dialog">
        <el-row :gutter="20">
          <!-- 左侧结果目录树 -->
          <el-col :span="8">
            <div class="folder-tree-panel">
              <div class="panel-header">
                <h4>结果目录结构</h4>
                <el-button type="primary" link @click="refreshFolderTree" :loading="folderTreeLoading">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  刷新
                </el-button>
              </div>
              <div class="tree-container">
                <el-tree ref="folderTreeRef" :data="folderTreeData" :props="folderTreeProps" :load="loadFolderTree" lazy
                  node-key="id" :expand-on-click-node="false" :highlight-current="true"
                  @node-click="handleFolderTreeNodeClick" v-loading="folderTreeLoading">
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <el-icon v-if="data.type === 'dir'">
                        <Folder />
                      </el-icon>
                      <el-icon v-else>
                        <Document />
                      </el-icon>
                      <span>{{ node.label }}</span>
                    </span>
                  </template>
                </el-tree>
              </div>
            </div>
          </el-col>

          <!-- 右侧文件列表 -->
          <el-col :span="16">
            <div class="file-list-panel">
              <div class="panel-header">
                <h4>文件列表
                  <span v-if="currentFolder" class="current-folder">- {{ currentFolder.name }}</span>
                </h4>
                <el-form :model="fileSelectionQuery" ref="fileSelectionQueryRef" size="small" :inline="true">
                  <el-form-item>
                    <el-input v-model="fileSelectionQuery.name" placeholder="农业输入数据名称搜索" clearable
                      @keyup.enter="handleFileSelectionSearch" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" icon="Search" @click="handleFileSelectionSearch">搜索</el-button>
                    <el-button icon="Refresh" @click="resetFileSelectionQuery">重置</el-button>
                  </el-form-item>
                </el-form>
              </div>

              <!-- 修复Bug 1 & 2: 增加 row-key 和 reserve-selection 支持跨页/跨结果目录多选 -->
              <el-table :data="fileSelectionList" v-loading="fileSelectionLoading"
                @selection-change="handleFileSelectionChange" ref="fileSelectionTableRef" height="400" row-key="id">
                <!-- reserve-selection 必须配合 row-key 使用 -->
                <el-table-column type="selection" :reserve-selection="true" width="55" />
                <el-table-column label="文件名称" prop="name" />
                <el-table-column label="文件大小" prop="size" width="120">
                  <template #default="scope">
                    {{ formatFileSize(scope.row.size) }}
                  </template>
                </el-table-column>
                <el-table-column label="文件类型" prop="type" width="120" />
                <el-table-column label="创建时间" prop="uploadTime" width="180">
                  <template #default="scope">
                    {{ parseTime(scope.row.uploadTime) }}
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination">
                <el-pagination v-model:current-page="fileSelectionQuery.pageNum"
                  v-model:page-size="fileSelectionQuery.pageSize" :page-sizes="[10, 20, 50]" :total="fileSelectionTotal"
                  layout="total, sizes, prev, pager, next" @size-change="handleFileSelectionSizeChange"
                  @current-change="handleFileSelectionCurrentChange" />
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="dialog-footer">
          <div class="selected-info">
            <div class="selected-count">
              已选择 {{ fileSelectionSelected.length }} 个文件
            </div>
            <div v-if="fileSelectionSelected.length > 0" class="selected-preview">
              <el-tag v-for="file in fileSelectionSelected.slice(0, 3)" :key="file.id" size="small" closable
                @close="removeFileSelection(file.id)" style="margin-right: 5px; margin-bottom: 5px;">
                {{ file.name }}
              </el-tag>
              <span v-if="fileSelectionSelected.length > 3" class="more-files">
                等 {{ fileSelectionSelected.length }} 个文件
              </span>
            </div>
          </div>
          <div>
            <el-button @click="fileSelectionDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="confirmFileSelection">确认选择</el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 单个文件参数选择对话框  -->
    <el-dialog
      v-model="fileParamDialogVisible"
      title="选择文件参数"
      width="1080px"
      append-to-body
      class="analysis-file-dialog"
    >
      <div class="file-param-dialog">
        <el-row :gutter="20">
          <!-- 左侧结果目录树 -->
          <el-col :span="8">
            <div class="folder-tree-panel">
              <div class="panel-header">
                <h4>结果目录结构</h4>
              </div>
              <div class="tree-container">
                <el-tree ref="fileParamTreeRef" :data="fileParamTreeData" :props="folderTreeProps"
                  :load="loadFileParamTree" lazy node-key="id" :expand-on-click-node="false" :highlight-current="true"
                  @node-click="handleFileParamTreeNodeClick" v-loading="fileParamTreeLoading">
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <el-icon v-if="data.type === 'dir'">
                        <Folder />
                      </el-icon>
                      <el-icon v-else>
                        <Document />
                      </el-icon>
                      <span>{{ node.label }}</span>
                    </span>
                  </template>
                </el-tree>
              </div>
            </div>
          </el-col>

          <!-- 右侧文件列表 -->
          <el-col :span="16">
            <div class="file-list-panel">
              <div class="panel-header">
                <h4>文件列表
                  <span v-if="fileParamCurrentFolder" class="current-folder">- {{ fileParamCurrentFolder.name }}</span>
                </h4>
                <el-form :model="fileParamQuery" ref="fileParamQueryRef" size="small" :inline="true">
                  <el-form-item>
                    <el-input v-model="fileParamQuery.name" placeholder="农业输入数据名称搜索" clearable
                      @keyup.enter="handleFileParamSearch" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" icon="Search" @click="handleFileParamSearch">搜索</el-button>
                    <el-button icon="Refresh" @click="resetFileParamQuery">重置</el-button>
                  </el-form-item>
                </el-form>
              </div>

              <el-table :data="fileParamList" v-loading="fileParamLoading" @row-click="handleFileParamRowClick"
                height="400">
                <el-table-column label="文件名称" prop="name" />
                <el-table-column label="文件大小" prop="size" width="120">
                  <template #default="scope">
                    {{ formatFileSize(scope.row.size) }}
                  </template>
                </el-table-column>
                <el-table-column label="文件类型" prop="type" width="120" />
                <el-table-column label="创建时间" prop="uploadTime" width="180">
                  <template #default="scope">
                    {{ parseTime(scope.row.uploadTime) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="scope">
                    <el-button type="primary" link @click="selectFileParam(scope.row)">选择</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination">
                <el-pagination v-model:current-page="fileParamQuery.pageNum" v-model:page-size="fileParamQuery.pageSize"
                  :page-sizes="[10, 20, 50]" :total="fileParamTotal" layout="total, sizes, prev, pager, next"
                  @size-change="handleFileParamSizeChange" @current-change="handleFileParamCurrentChange" />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>

    <!-- 结果数据/报告列表对话框 -->
    <el-dialog
      v-model="fileDialogVisible"
      :title="`分析结果数据/报告 - ${currentFolderName}`"
      width="980px"
      destroy-on-close
      class="analysis-result-dialog"
      @close="handleFileDialogClose">
      <div>
        <el-form :model="fileQueryParams" ref="fileQueryRef" size="small" :inline="true" @submit.native.prevent>
          <el-form-item label="文件名称">
            <el-input placeholder="文件名称" v-model="fileQueryParams.name"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" size="small" @click="handleFileQuery">搜索</el-button>
            <el-button icon="Refresh" size="small" @click="resetFileQuery">重置</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="fileDataList" border v-loading="fileLoading">
          <template #empty>
            <el-empty description="该分析结果目录暂无数据文件" />
          </template>

          <el-table-column align="center" prop="id" label="ID" width="80" />
          <el-table-column align="center" prop="name" label="名称" width="200" />
          <el-table-column align="center" prop="type" label="类型" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.type === 'dir' ? 'primary' : 'success'">
                {{ scope.row.type === 'dir' ? '结果目录' : '文件' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column align="center" prop="root" label="所属结果目录ID" width="120">
            <template #default="scope">
              <span>{{ scope.row.root }}</span>
            </template>
          </el-table-column>
          <el-table-column align="center" prop="size" label="大小" width="120">
            <template #default="scope">
              <div>
                <span v-if="scope.row.type === 'dir'">-</span>
                <span v-else>{{ formatFileSize(scope.row.size) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column align="center" label="操作" width="200">
            <template #default="scope">
              <!-- 结果目录操作 -->
              <template v-if="scope.row.type === 'dir'">
                <el-button type="text" @click="openSubFolder(scope.row)">打开</el-button>
              </template>
              <!-- 文件操作 -->
              <template v-else>
                <el-button type="text" @click="downloadFile(scope.row)">下载</el-button>
                <el-button type="text" @click="previewFile(scope.row)" v-if="isPreviewable(scope.row)">预览</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页组件 -->
        <div class="pagination" v-if="fileTotal > 0">
          <el-pagination v-model:current-page="fileQueryParams.pageNum" v-model:page-size="fileQueryParams.pageSize"
            :page-sizes="[5, 10, 20, 50]" :total="fileTotal" :pager-count="5"
            layout="total, sizes, prev, pager, next, jumper" @size-change="handleFileSizeChange"
            @current-change="handleFileCurrentChange" />
        </div>
      </div>
    </el-dialog>

    <!-- 预览对话框 (Bug 5 修复) -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="previewTitle"
      width="860px"
      append-to-body
      class="analysis-preview-dialog"
    >
      <div v-loading="previewLoading" class="preview-container">
        <!-- 图片预览 -->
        <div v-if="previewType === 'image'" style="text-align: center;">
          <img :src="previewContent" style="max-width: 100%; max-height: 500px;" />
        </div>
        <!-- 文本预览 -->
        <div v-else-if="previewType === 'text'">
          <pre
            style="white-space: pre-wrap; word-wrap: break-word; background: rgba(3, 20, 34, 0.9); color: #eefaff; padding: 10px; max-height: 500px; overflow-y: auto;">
        {{ previewContent }}</pre>
        </div>
        <div v-else>
          <el-empty description="暂不支持该格式预览" />
        </div>
      </div>
    </el-dialog>

  </div>
</template>

<script setup name="AgricultureAnalysisTask">
import AgriPageHeader from '@/components/AgriPageHeader'
import { listTask, getTask, delTask, addTask, updateTask, executeTask } from "@/api/task/task";
import { listFile, down } from "@/api/file/file";
import { listContainer } from "@/api/container/container";
import { listAlgorithm } from "@/api/container/container";
import { FolderOpened, Plus, Delete, VideoPlay, Loading, Folder, Document, Refresh, Search } from '@element-plus/icons-vue'
import { getCurrentInstance, reactive, ref, toRefs, onUnmounted } from 'vue';

const { proxy } = getCurrentInstance();

// 预览相关变量
const previewDialogVisible = ref(false);
const previewTitle = ref('文件预览');
const previewType = ref('');
const previewContent = ref('');
const previewLoading = ref(false);

const fileSelectionDialogVisible = ref(false);
const currentFolderName = ref('');
const selectedFiles = ref([]);
const fileSelectionSelected = ref([]);
const fileSelectionLoading = ref(false);
const fileSelectionList = ref([]);
const fileSelectionTotal = ref(0);
const fileParamDialogVisible = ref(false);
const fileParamLoading = ref(false);
const fileParamList = ref([]);
const fileParamTotal = ref(0);
const fileSelectionTableRef = ref();
const folderTreeRef = ref();
const folderTreeData = ref([]);
const folderTreeLoading = ref(false);
const folderTreeProps = ref({
  label: 'name',
  children: 'children',
  isLeaf: 'isLeaf'
});
const currentFolder = ref(null);
const fileParamCurrentFolder = ref(null);
const fileParamTreeRef = ref();
const fileParamTreeData = ref([]);
const fileParamTreeLoading = ref(false);
const taskList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const title = ref("");
const currentStep = ref(0);
const containerLoading = ref(false);
const algorithmLoading = ref(false);
const fileDialogVisible = ref(false);
const fileLoading = ref(false);
const fileDataList = ref([]);
const fileTotal = ref(0);
const currentFolderId = ref('');
const pollingRetryCounts = ref({});
const pollingIntervals = ref({});
const emptyStateCounts = ref({});
const containers = ref([]);
const algorithms = ref([]);
const containerAlgorithms = ref({});
const pollingStartTimes = ref({});
const algorithmParams = ref([]);
const currentFileParam = ref(null); // 添加遗漏的变量

const fileSelectionQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  name: null,
  root: '0' // 默认根目录
});
const fileParamQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  name: null,
  root: '0'
});
const data = reactive({
  form: {
    id: null,
    name: null,
    container: null,
    algo: null,
    args: null,
    argstr: null,
    params: [],
    file_ids: '',
    remark: null,
    state: null,
    result: null,
    init_time: null,
    end_time: null,
    dept: null,
  },
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: null,
    container: null,
    algo: null,
    remark: null,
    state: null,
  },
  fileQueryParams: {
    pageNum: 1,
    pageSize: 10,
    name: null,
    root: null
  },
  rules: {
    name: [
      { required: true, message: "分析任务名称不能为空", trigger: "blur" }
    ],
    container: [
      { required: true, message: "算法服务不能为空", trigger: "change" }
    ],
    algo: [
      { required: true, message: "农业模型/农业模型/算法不能为空", trigger: "change" }
    ]
  }
});

const { queryParams, form, rules, fileQueryParams } = toRefs(data);

/** 重置文件列表查询 */
function resetFileQuery() {
  fileQueryParams.value.name = null;
  fileQueryParams.value.pageNum = 1;
  getFileList();
}

/** 打开子结果目录 */
function openSubFolder(folder) {
  if (folder.type !== 'dir') {
    return;
  }

  currentFolderId.value = folder.id;
  currentFolderName.value = `${currentFolderName.value} / ${folder.name}`;

  // 更新查询参数
  fileQueryParams.value.root = folder.id;
  fileQueryParams.value.pageNum = 1;

  getFileList();
}

/** 查询农业分析任务列表 */
function getList() {
  loading.value = true;
  listTask(queryParams.value).then(response => {
    taskList.value = response.rows;
    total.value = response.total;
    loading.value = false;
  });
}

/** 加载容器列表 */
function loadContainers() {
  containerLoading.value = true;
  listContainer().then(response => {
    containers.value = response.rows || response.data || [];
    containerLoading.value = false;
  }).catch(() => {
    containerLoading.value = false;
  });
}

/** 加载算法列表 */
function loadAlgorithms(containerId) {
  if (!containerId) return Promise.resolve(); // 修复未返回 Promise 问题
  algorithmLoading.value = true;
  return listAlgorithm(containerId).then(response => {
    if (response && response.data && typeof response.data === 'object') {
      const algorithmsArray = Object.entries(response.data).map(([algo_name, algoInfo]) => {
        const { parameters, parameters_intro, hasValidParams } = validateAndProcessAlgorithmParams(algoInfo);

        return {
          id: algo_name,
          algo_name: algo_name,
          name: algo_name,
          type: '自定义算法',
          version: '1.0',
          intro: algoInfo.intro || '',
          args_intro: algoInfo.args_intro || '{}',
          args: algoInfo.args || '{}',
          container_id: containerId,
          parameters: parameters,
          parameters_intro: parameters_intro,
          hasValidParams: hasValidParams
        };
      });
      containerAlgorithms.value[containerId] = algorithmsArray;
    } else {
      containerAlgorithms.value[containerId] = [];
      console.warn('响应数据格式异常:', response);
    }

    algorithmLoading.value = false;
  }).catch((error) => {
    console.error('获取算法列表失败:', error);
    algorithmLoading.value = false;
  });
}

/** 加载结果目录树 */
function loadFolderTree(node, resolve) {
  if (node.level === 0) {
    // 根节点，通常由 refreshFolderTree 手动加载，或者这里首次加载
    // 如果已经有数据，直接resolve空，防止重复
    if (folderTreeData.value.length > 0) {
      return resolve([]);
    }
    loadRootFolders().then(data => {
      folderTreeData.value = data; // 显式赋值
      resolve(data);
    });
  } else {
    loadChildFolders(node.data.id).then(data => {
      resolve(data);
    });
  }
}

/** 加载文件参数结果目录树 */
function loadFileParamTree(node, resolve) {
  if (node.level === 0) {
    loadRootFolders().then(data => {
      fileParamTreeData.value = data;
      resolve(data);
    });
  } else {
    loadChildFolders(node.data.id).then(data => {
      resolve(data);
    });
  }
}

/** 加载根目录结果目录 (修复 Bug 3: 根目录重复) */
function loadRootFolders() {
  return new Promise((resolve) => {
    const query = {
      pageNum: 1,
      pageSize: 1000,
      type: 'dir',
      root: '0'
    };

    listFile(query).then(response => {
      let data = [];
      if (response.rows) {
        data = response.rows;
      } else if (response.data) {
        data = response.data;
      }
      // 修复根目录判断逻辑：root 为 0, "0", 或 null 都视为根目录
      const folders = data.filter(item => item.type === 'dir' && (item.root == 0 || item.root === '0' || item.root === null));
      const treeData = folders.map(folder => ({
        ...folder,
        isLeaf: false
      }));

      resolve(treeData);
    }).catch(error => {
      console.error('加载根目录失败:', error);
      resolve([]);
    });
  });
}

/** 加载子结果目录 */
function loadChildFolders(parentId) {
  return new Promise((resolve) => {
    const query = {
      pageNum: 1,
      pageSize: 1000,
      type: 'dir',
      root: parentId
    };

    listFile(query).then(response => {
      let data = [];
      if (response.rows) {
        data = response.rows;
      } else if (response.data) {
        data = response.data;
      }

      const folders = data.filter(item => item.type === 'dir');
      const treeData = folders.map(folder => ({
        ...folder,
        isLeaf: false
      }));

      resolve(treeData);
    }).catch(error => {
      console.error('加载子结果目录失败:', error);
      resolve([]);
    });
  });
}

/** 结果目录树节点点击事件 */
function handleFolderTreeNodeClick(data) {
  if (data.type === 'dir') {
    currentFolder.value = data;
    fileSelectionQuery.root = data.id;
    fileSelectionQuery.pageNum = 1;
    loadFileSelectionList();
  }
}

/** 文件参数结果目录树节点点击事件 */
function handleFileParamTreeNodeClick(data) {
  if (data.type === 'dir') {
    fileParamCurrentFolder.value = data;
    fileParamQuery.root = data.id;
    fileParamQuery.pageNum = 1;
    loadFileParamList();
  }
}

/** 刷新结果目录树 */
function refreshFolderTree() {
  folderTreeLoading.value = true;
  // 先清空，避免 lazy loading 导致重复
  folderTreeData.value = [];
  loadRootFolders().then(data => {
    folderTreeData.value = data;
    folderTreeLoading.value = false;
  }).catch(() => {
    folderTreeLoading.value = false;
  });
}

/** 打开文件选择对话框 (修复 Bug 1) */
function openFileSelectionDialog() {
  fileSelectionDialogVisible.value = true;
  fileSelectionSelected.value = []; // 清空临时选择数组

  // 重要：清除表格的选中状态，防止"保存上一次选的状态"
  if (fileSelectionTableRef.value) {
    fileSelectionTableRef.value.clearSelection();
  }

  // 重置根目录查询
  fileSelectionQuery.root = '0';
  fileSelectionQuery.pageNum = 1;
  currentFolder.value = { id: '0', name: '根目录' };

  // 刷新树
  refreshFolderTree();
  // 初始加载文件列表
  loadFileSelectionList();
}

/** 加载文件选择列表 */
function loadFileSelectionList() {
  fileSelectionLoading.value = true;
  const query = {
    ...fileSelectionQuery,
    type: 'image' // 这里原本是image，如果想选所有文件可能需要改
  };

  // 移除 type 限制，除非业务明确只选 image
  // delete query.type; 

  listFile(query).then(response => {
    let data = [];
    if (response.rows) {
      data = response.rows;
    } else if (response.data) {
      data = response.data;
    }
    // 过滤结果目录
    fileSelectionList.value = data.filter(item =>
      item.type !== 'dir' &&
      item.size !== null &&
      item.size > 0
    ).map(file => ({
      ...file,
      folderPath: currentFolder.value ? currentFolder.value.name : '根目录'
    }));

    fileSelectionTotal.value = response.total || fileSelectionList.value.length;
    fileSelectionLoading.value = false;
  }).catch(error => {
    console.error('加载文件列表失败:', error);
    fileSelectionLoading.value = false;
  });
}

/** 文件选择变化 (修复 Bug 2: 跨页/跨结果目录选择) */
function handleFileSelectionChange(selection) {
  // 因为使用了 reserve-selection，selection 包含所有已选的行（跨页/跨结果目录）
  fileSelectionSelected.value = selection;
}

/** 移除文件选择 */
function removeFileSelection(fileId) {
  // 从临时数组中移除
  const index = fileSelectionSelected.value.findIndex(file => file.id === fileId);
  if (index > -1) {
    fileSelectionSelected.value.splice(index, 1);
  }

  // 同步取消表格勾选
  if (fileSelectionTableRef.value) {
    const row = fileSelectionList.value.find(item => item.id === fileId);
    if (row) {
      fileSelectionTableRef.value.toggleRowSelection(row, false);
    } else {
      // 如果当前页找不到该行（在其他结果目录），Element Plus 的 reserve-selection 会自动处理
      // 但我们需要手动更新表格状态（如果它被缓存了）
      // 对于 row-key + reserve-selection，直接操作数据源通常不够，需要操作 selection 数组
      // 上面的 splice 已经移除了数据，但 table 内部状态可能还在
      // 实际上 handleFileSelectionChange 是单向的 Table -> Data
      // 如果要 Data -> Table 反向操作，对于不在当前视图的行比较麻烦
      // 这里简单处理：toggleRowSelection 只能处理当前视图
    }
  }
}

/** 确认文件选择 */
function confirmFileSelection() {
  // 合并到主列表，去重
  const newFiles = fileSelectionSelected.value.filter(newFile =>
    !selectedFiles.value.some(existingFile => existingFile.id === newFile.id)
  );

  selectedFiles.value = [...selectedFiles.value, ...newFiles];
  fileSelectionDialogVisible.value = false;

  proxy.$modal.msgSuccess(`已添加 ${newFiles.length} 个文件`);
}

function removeSelectedFile(fileId) {
  selectedFiles.value = selectedFiles.value.filter(file => file.id !== fileId);
}

/** 打开文件参数选择对话框 */
function openFileParamSelection(param) {
  currentFileParam.value = param;
  fileParamDialogVisible.value = true;
  // 加载树
  if (fileParamTreeData.value.length === 0) {
    loadRootFolders().then(data => {
      fileParamTreeData.value = data;
    });
  }

  fileParamQuery.root = '0';
  fileParamQuery.pageNum = 1;
  fileParamCurrentFolder.value = { id: '0', name: '根目录' };
  loadFileParamList();
}

/** 加载文件参数列表 */
function loadFileParamList() {
  fileParamLoading.value = true;

  const query = {
    ...fileParamQuery,
    type: 'file'
  };

  listFile(query).then(response => {
    let data = [];
    if (response.rows) {
      data = response.rows;
    } else if (response.data) {
      data = response.data;
    }

    fileParamList.value = data.filter(item =>
      item.type !== 'dir' &&
      item.size !== null &&
      item.size > 0
    );

    fileParamTotal.value = response.total || fileParamList.value.length;
    fileParamLoading.value = false;
  }).catch(error => {
    console.error('加载文件参数列表失败:', error);
    fileParamLoading.value = false;
  });
}

/** 选择文件参数 */
function selectFileParam(file) {
  if (currentFileParam.value) {
    currentFileParam.value.value = file.id;
    fileParamDialogVisible.value = false;
    proxy.$modal.msgSuccess(`已选择文件: ${file.name}`);
  }
}

/** 文件参数行点击 */
function handleFileParamRowClick(row) {
  selectFileParam(row);
}

/** 根据文件ID获取文件名 */
function getFileNameById(fileId) {
  const file = selectedFiles.value.find(f => f.id === fileId);
  if (file) return file.name;
  const paramFile = fileParamList.value.find(f => f.id === fileId);
  if (paramFile) return paramFile.name;

  return `文件ID: ${fileId}`;
}

/** 参数类型变化处理 */
function onParamTypeChange(param) {
  if (param.type === 'file') {
    param.value = '';
  }
}
function getParamRules(param) {
  const baseRule = { required: true, message: '参数值不能为空', trigger: 'blur' };

  if (param.type === 'file') {
    return [
      baseRule,
      {
        validator: (rule, value, callback) => {
          if (!value) {
            callback(new Error('请选择文件'));
          } else {
            callback();
          }
        },
        trigger: 'change'
      }
    ];
  }

  return [baseRule];
}

/** 文件选择搜索 */
function handleFileSelectionSearch() {
  fileSelectionQuery.pageNum = 1;
  loadFileSelectionList();
}

/** 重置文件选择查询 */
function resetFileSelectionQuery() {
  fileSelectionQuery.name = null;
  fileSelectionQuery.pageNum = 1;
  loadFileSelectionList();
}

/** 文件选择分页大小改变 */
function handleFileSelectionSizeChange(val) {
  fileSelectionQuery.pageSize = val;
  fileSelectionQuery.pageNum = 1;
  loadFileSelectionList();
}

/** 文件选择当前页改变 */
function handleFileSelectionCurrentChange(val) {
  fileSelectionQuery.pageNum = val;
  loadFileSelectionList();
}

/** 文件参数搜索 */
function handleFileParamSearch() {
  fileParamQuery.pageNum = 1;
  loadFileParamList();
}

/** 重置文件参数查询 */
function resetFileParamQuery() {
  fileParamQuery.name = null;
  fileParamQuery.pageNum = 1;
  loadFileParamList();
}

/** 文件参数分页大小改变 */
function handleFileParamSizeChange(val) {
  fileParamQuery.pageSize = val;
  fileParamQuery.pageNum = 1;
  loadFileParamList();
}

/** 文件参数当前页改变 */
function handleFileParamCurrentChange(val) {
  fileParamQuery.pageNum = val;
  loadFileParamList();
}

/** 准备模型运行参数*/
function prepareTaskArgs() {
  const argsObject = {
    args: []
  };

  const paramsObj = {};
  form.value.params.forEach(param => {
    if (param.name === 'input' || param.name === 'Input' || param.name === 'INPUT') {
      return;
    }

    if (param.name && param.value !== undefined && param.value !== '') {
      let value = param.value;
      switch (param.type) {
        case 'int':
          value = parseInt(value);
          if (isNaN(value)) value = param.value;
          break;
        case 'float':
          value = parseFloat(value);
          if (isNaN(value)) value = param.value;
          break;
        case 'bool':
          value = value.toLowerCase() === 'true';
          break;
        case 'file':
          value = String(value);
          break;
      }

      paramsObj[param.name] = value;
    }
  });
  if (selectedFiles.value.length > 0) {
    const fileIdArray = selectedFiles.value.map(file => file.id);
    paramsObj['file_ids'] = fileIdArray;
    form.value.file_ids = fileIdArray.join(',');
  }
  argsObject.args.push(paramsObj);
  return {
    args: JSON.stringify(argsObject),
    argstr: JSON.stringify(paramsObj)
  };
}

/** 重置 */
function reset() {
  form.value = {
    id: null,
    name: null,
    container: null,
    algo: null,
    args: null,
    argstr: null,
    params: [],
    file_ids: '',
    remark: null,
    state: null,
    result: null,
    init_time: null,
    end_time: null,
    dept: null,
  };
  selectedFiles.value = [];
  algorithmParams.value = [];
  proxy.resetForm("taskRef");
  currentStep.value = 0;
}


/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const _id = row.id || ids.value;
  getTask(_id).then(response => {
    form.value = response.data;
    if (form.value.args && typeof form.value.args === 'string') {
      try {
        const parsedArgs = JSON.parse(form.value.args);
        if (parsedArgs.args && Array.isArray(parsedArgs.args) && parsedArgs.args.length > 0) {
          const firstArgObj = parsedArgs.args[0];
          if (firstArgObj.file_ids && Array.isArray(firstArgObj.file_ids)) {
            selectedFiles.value = firstArgObj.file_ids.map(id => ({
              id: id,
              name: `文件ID: ${id}`,
              size: 0
            }));
          }

          form.value.params = Object.entries(firstArgObj)
            .filter(([key]) => key !== 'file_ids' && key !== 'input' && key !== 'Input' && key !== 'INPUT')
            .map(([name, value]) => {
              const isFileId = typeof value === 'string' && value.length > 0 && !isNaN(value);

              return {
                name,
                type: isFileId ? 'file' : getParamType(value),
                value: String(value)
              };
            });
        } else {
          form.value.params = Object.entries(parsedArgs)
            .filter(([key]) => key !== 'input' && key !== 'Input' && key !== 'INPUT')
            .map(([name, value]) => {
              return {
                name,
                type: getParamType(value),
                value: String(value)
              };
            });
        }
      } catch (e) {
        console.error('解析模型运行参数失败:', e);
        form.value.params = [];
      }
    }

    open.value = true;
    title.value = "修改分析任务";
    currentStep.value = 3;
    loadContainers();
    if (form.value.container) {
      loadAlgorithms(form.value.container).then(() => {
        if (form.value.algo) {
          onAlgorithmSelect();
        }
      });
    }
  });
}

/** 运行农业分析 */
function handleExecute(row) {
  if (row.state === 'running') {
    proxy.$modal.msgWarning('任务正在执行中，请勿重复执行');
    return;
  }

  proxy.$modal.confirm('确认要运行农业分析 "' + row.name + '" 吗？').then(function () {
    const taskIndex = taskList.value.findIndex(item => item.id === row.id);
    if (taskIndex !== -1) {
      taskList.value[taskIndex].state = 'running';
      taskList.value[taskIndex].result = null;
    }
    return executeTask(row.id);
  }).then((response) => {
    if (response.code === 200) {
      proxy.$modal.msgSuccess("任务开始执行");
      setTimeout(() => {
        startPollingTaskStatus(row.id);
      }, 3000);

    } else {
      proxy.$modal.msgError("任务执行失败: " + (response.msg || '未知错误'));
      const taskIndex = taskList.value.findIndex(item => item.id === row.id);
      if (taskIndex !== -1) {
        taskList.value[taskIndex].state = 'failed';
      }
    }
  }).catch((error) => {
    const taskIndex = taskList.value.findIndex(item => item.id === row.id);
    if (taskIndex !== -1) {
      taskList.value[taskIndex].state = 'failed';
    }
    proxy.$modal.msgError("任务执行失败");
  });
}

/** 轮询运行状态 */
function startPollingTaskStatus(taskId) {
  pollingStartTimes.value[taskId] = Date.now();
  pollingRetryCounts.value[taskId] = 0;
  emptyStateCounts.value[taskId] = 0;
  if (pollingIntervals.value[taskId]) {
    clearInterval(pollingIntervals.value[taskId]);
    delete pollingIntervals.value[taskId];
  }
  const forceStopTimer = setTimeout(() => {
    stopPollingTaskStatus(taskId);
    const taskIndex = taskList.value.findIndex(item => item.id === taskId);
    if (taskIndex !== -1) {
      taskList.value[taskIndex].state = 'unknown';
    }
    proxy.$modal.msgWarning('任务执行超时，状态未知');
  }, 5 * 60 * 6000);
  pollingIntervals.value[taskId] = {
    interval: null,
    forceStop: forceStopTimer
  };
  updateTaskStatus(taskId);
  pollingIntervals.value[taskId].interval = setInterval(() => {
    updateTaskStatus(taskId);
  }, 5000);
}

/** 轮询运行状态 */
async function updateTaskStatus(taskId) {
  try {
    const taskResponse = await getTask(taskId);
    const task = taskResponse.data;
    pollingRetryCounts.value[taskId] = (pollingRetryCounts.value[taskId] || 0) + 1;
    const taskIndex = taskList.value.findIndex(item => item.id === taskId);
    if (taskIndex !== -1) {
      taskList.value[taskIndex] = {
        ...taskList.value[taskIndex],
        state: task.state || 'unknown',
        result: task.result,
        end_time: task.end_time
      };
    }

    const maxTotalRetries = 120;
    const hasValidResult = task.result && task.result !== 'null' && task.result !== 'None';

    if (task.state === 'completed' || task.state === 'success' || hasValidResult) {
      stopPollingTaskStatus(taskId);
      proxy.$message.success(`任务 "${task.name}" 执行完成`);
    }
    else if (task.state === 'failed') {
      stopPollingTaskStatus(taskId);
      proxy.$message.error(`任务 "${task.name}" 执行失败`);
    }
    else if (pollingRetryCounts.value[taskId] >= maxTotalRetries) {
      stopPollingTaskStatus(taskId);
    }
  } catch (error) {
    console.error('获取运行状态失败:', error);
  }
}

/** 停止轮询运行状态 */
function stopPollingTaskStatus(taskId) {
  if (pollingIntervals.value[taskId]) {
    if (pollingIntervals.value[taskId].interval) {
      clearInterval(pollingIntervals.value[taskId].interval);
    }
    if (pollingIntervals.value[taskId].forceStop) {
      clearTimeout(pollingIntervals.value[taskId].forceStop);
    }
    delete pollingIntervals.value[taskId];
  }
  if (pollingStartTimes.value[taskId]) {
    delete pollingStartTimes.value[taskId];
  }
}


// 组件卸载时清除所有轮询
onUnmounted(() => {
  Object.values(pollingIntervals.value).forEach(interval => {
    if (interval.interval) clearInterval(interval.interval);
    if (interval.forceStop) clearTimeout(interval.forceStop);
  });
  pollingIntervals.value = {};
});

function openResultFolder(folderId, taskName = '') {
  if (!folderId || folderId === 'null' || folderId === 'None') {
    proxy.$modal.msgWarning('该任务暂无结果');
    return;
  }

  const actualFolderId = String(folderId).trim();
  if (!actualFolderId || actualFolderId === '0') {
    proxy.$modal.msgWarning('无效的结果目录ID');
    return;
  }

  currentFolderId.value = actualFolderId;
  currentFolderName.value = taskName ? `分析结果 - ${taskName}` : `分析结果 - 结果目录ID: ${actualFolderId}`;

  // 重置分页参数
  fileQueryParams.value.pageNum = 1;
  fileQueryParams.value.pageSize = 10;
  fileQueryParams.value.name = null;
  fileQueryParams.value.root = actualFolderId;

  getFileList();
  fileDialogVisible.value = true;
}


/** 获取文件列表 (修复 Bug 4: 移除前端过滤) */
function getFileList() {
  fileLoading.value = true;

  const query = {
    pageNum: fileQueryParams.value.pageNum,
    pageSize: fileQueryParams.value.pageSize,
    name: fileQueryParams.value.name || undefined,
    root: fileQueryParams.value.root
  };

  listFile(query).then(response => {
    let data = [];
    let total = 0;

    if (response.rows) {
      data = response.rows;
      total = response.total;
    } else if (response.data) {
      data = response.data;
      total = response.total;
    } else if (Array.isArray(response)) {
      data = response;
      total = data.length;
    }

    // 修复 Bug 4: 不在前端进行 root 过滤，假设后端已正确处理分页和筛选
    // 如果后端不支持筛选，分页肯定有问题，这是后端逻辑
    fileDataList.value = data;
    fileTotal.value = total;
    fileLoading.value = false;

  }).catch((error) => {
    console.error('获取文件列表失败:', error);
    fileLoading.value = false;
    proxy.$modal.msgError('获取文件列表失败: ' + (error.message || '未知错误'));
  });
}


/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
  currentStep.value = 0;
}


/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

/** 多选框选中数据  */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = "添加任务";
  currentStep.value = 0;
  // 加载容器列表
  loadContainers();
}


/** 容器变更处理 */
function onContainerChange() {
  form.value.algo = null;
  algorithmParams.value = [];
  form.value.params = [];
  loadAlgorithms(form.value.container);
}

/** 算法选择后的处理  */
function onAlgorithmSelect() {
  if (!form.value.container || !form.value.algo) return;
  const algoList = containerAlgorithms.value[form.value.container] || [];
  const selectedAlgo = algoList.find(algo => algo.name === form.value.algo);
  if (selectedAlgo) {
    algorithmParams.value = [];
    if (selectedAlgo.parameters && Object.keys(selectedAlgo.parameters).length > 0) {
      algorithmParams.value = Object.entries(selectedAlgo.parameters).map(([name, defaultValue]) => {
        const intro = selectedAlgo.parameters_intro && selectedAlgo.parameters_intro[name]
          ? selectedAlgo.parameters_intro[name]
          : '暂无说明';
        return {
          name,
          default: defaultValue,
          intro
        };
      });
      form.value.params = Object.entries(selectedAlgo.parameters)
        .filter(([name]) => name !== 'input' && name !== 'Input' && name !== 'INPUT')
        .map(([name, defaultValue]) => {
          return {
            name,
            type: getParamType(defaultValue),
            value: String(defaultValue)
          };
        });
    } else {
      algorithmParams.value = [];
      form.value.params = [];
    }
  } else {
    algorithmParams.value = [];
    form.value.params = [];
  }
}
/** 根据默认值推断参数类型  */
function getParamType(value) {
  if (value === null || value === undefined) return 'string';
  if (typeof value === 'boolean') return 'bool';
  if (Number.isInteger(value)) return 'int';
  if (typeof value === 'number') return 'float';
  if (typeof value === 'string') {
    if (value.toLowerCase() === 'true' || value.toLowerCase() === 'false') return 'bool';
    if (!isNaN(value) && value.trim() !== '') return 'float';
    return 'string';
  }
  return 'string';
}

/** 添加参数 */
function addParameter() {
  form.value.params.push({
    name: '',
    type: 'string',
    value: ''
  });
}

/** 删除参数 */
function removeParameter(index) {
  form.value.params.splice(index, 1);
}

/** 验证模型运行参数  */
function validateTaskArgs() {
  const paramNames = form.value.params.map(param => param.name);
  const uniqueNames = new Set(paramNames);
  if (uniqueNames.size !== paramNames.length) {
    proxy.$modal.msgError("参数名称不能重复");
    return false;
  }

  for (let i = 0; i < form.value.params.length; i++) {
    const param = form.value.params[i];

    if (!param.name || param.name.trim() === '') {
      proxy.$modal.msgError(`参数 ${i + 1} 的名称不能为空`);
      return false;
    }

    if (param.name === 'input' || param.name === 'Input' || param.name === 'INPUT') {
      continue;
    }

    if (param.value === undefined || param.value === '') {
      proxy.$modal.msgError(`参数 "${param.name}" 的值不能为空`);
      return false;
    }

    if (param.type === 'int' || param.type === 'float') {
      const numValue = parseFloat(param.value);
      if (isNaN(numValue)) {
        proxy.$modal.msgError(`参数 "${param.name}" 必须是有效的数字`);
        return false;
      }
    }

    if (param.type === 'bool') {
      const lowerValue = param.value.toLowerCase();
      if (lowerValue !== 'true' && lowerValue !== 'false') {
        proxy.$modal.msgError(`参数 "${param.name}" 必须是 true 或 false`);
        return false;
      }
    }
  }

  return true;
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["taskRef"].validate(valid => {
    if (valid) {

      if (!validateTaskArgs()) {
        return;
      }

      const taskParams = prepareTaskArgs();
      form.value.args = taskParams.args;
      form.value.argstr = taskParams.argstr;
      if (form.value.id != null) {
        updateTask(form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        }).catch(error => {
          console.error('更新任务失败:', error);
          proxy.$modal.msgError("更新任务失败: " + (error.message || '未知错误'));
        });
      } else {
        addTask(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功");
          open.value = false;
          getList();
        }).catch(error => {
          console.error('新建分析任务失败:', error);
          proxy.$modal.msgError("新建分析任务失败: " + (error.message || '未知错误'));
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const _ids = row.id || ids.value;
  proxy.$modal.confirm('是否确认删除分析任务编号为"' + _ids + '"的数据项？').then(function () {
    return delTask(_ids);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => { });
}

/** 获取容器名称 */
function getContainerName(containerId) {
  const container = containers.value.find(c => c.id === containerId);
  return container ? container.name : `算法服务 ${containerId}`;
}

function getStatusText(status, result) {
  if (result && result !== 'null' && result !== 'None') {
    return '已完成';
  }
  if (!status || status === 'null' || status === 'None') {
    return '状态未知';
  }

  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'unknown': '状态未知',
    'error': '查询错误'
  };
  return statusMap[status] || status || '状态未知';
}

function getStatusType(status, result) {
  if (result && result !== 'null' && result !== 'None') {
    return 'success';
  }
  if (!status || status === 'null' || status === 'None') {
    return 'warning';
  }
  const typeMap = {
    'pending': 'warning',
    'running': 'primary',
    'completed': 'success',
    'failed': 'danger',
    'unknown': 'warning',
    'error': 'danger'
  };
  return typeMap[status] || 'info';
}

/** 格式化参数显示 */
function formatArgs(args) {
  if (!args) return '无参数';
  try {
    const parsed = JSON.parse(args);
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    return args;
  }
}

/** 根据参数类型获取占位符文本 */
function getParamPlaceholder(type) {
  const placeholderMap = {
    'string': '请输入字符串',
    'int': '请输入整数',
    'float': '请输入浮点数',
    'bool': 'true 或 false'
  };
  return placeholderMap[type] || '请输入值';
}


/** 文件列表搜索 */
function handleFileQuery() {
  fileQueryParams.value.pageNum = 1;
  getFileList();
}


/** 文件列表分页大小改变 */
function handleFileSizeChange(val) {
  fileQueryParams.value.pageSize = val;
  fileQueryParams.value.pageNum = 1;
  getFileList();
}

/** 文件列表当前页改变 */
function handleFileCurrentChange(val) {
  fileQueryParams.value.pageNum = val;
  getFileList();
}

/** 文件对话框关闭处理 */
function handleFileDialogClose() {
  fileDataList.value = [];
  fileTotal.value = 0;
  currentFolderId.value = '';
  currentFolderName.value = '';

  // 重置查询参数
  fileQueryParams.value.pageNum = 1;
  fileQueryParams.value.pageSize = 10;
  fileQueryParams.value.name = null;
  fileQueryParams.value.root = null;
}


/** 格式化文件大小 */
function formatFileSize(size) {
  if (!size && size !== 0) return '-';

  if (size < 1024) {
    return size + ' B';
  } else if (size < 1024 * 1024) {
    return (size / 1024).toFixed(2) + ' KB';
  } else if (size < 1024 * 1024 * 1024) {
    return (size / (1024 * 1024)).toFixed(2) + ' MB';
  } else {
    return (size / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }
}

/** 下载文件 */
async function downloadFile(file) {
  try {
    if (!file || !file.id) {
      proxy.$modal.msgError("无法获取文件信息");
      return;
    }

    const loading = proxy.$loading({
      lock: true,
      text: `正在下载: ${file.name}`,
      background: 'rgba(0, 0, 0, 0.7)'
    });

    const blobData = await down(file.id);

    if (!blobData || blobData.size === 0) {
      throw new Error('文件内容为空');
    }
    const url = window.URL.createObjectURL(blobData);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    proxy.$modal.msgSuccess(`下载完成: ${file.name}`);

  } catch (error) {
    console.error('下载失败:', error);
    proxy.$modal.msgError(`下载失败: ${error.message}`);
  } finally {
    proxy.$loading().close();
  }
}
/** 验证并处理算法参数 */
function validateAndProcessAlgorithmParams(algoInfo) {
  const result = {
    parameters: {},
    parameters_intro: {},
    hasValidParams: false
  };

  try {
    if (algoInfo.args && typeof algoInfo.args === 'string') {
      if (algoInfo.args.trim().startsWith('{') || algoInfo.args.trim().startsWith('[')) {
        result.parameters = JSON.parse(algoInfo.args);
        result.hasValidParams = true;
      } else {
        result.parameters = {
          input: 'default'
        };
        result.parameters_intro = {
          input: algoInfo.args || '算法输入参数'
        };
      }
    }
  } catch (e) {
    console.warn('参数解析失败，使用默认参数:', e.message);
    result.parameters = {
      input: 'default'
    };
    result.parameters_intro = {
      input: '算法输入参数'
    };
  }

  try {
    if (algoInfo.intro && typeof algoInfo.intro === 'string') {
      if (algoInfo.intro.trim().startsWith('{')) {
        result.parameters_intro = JSON.parse(algoInfo.intro);
      } else {
        Object.keys(result.parameters).forEach(key => {
          result.parameters_intro[key] = algoInfo.intro;
        });
      }
    }
  } catch (e) {
    console.warn('参数说明解析失败:', e.message);
  }

  return result;
}

/** 预览文件 (Bug 5 修复) */
async function previewFile(file) {
  if (!isPreviewable(file)) {
    proxy.$message.warning('该文件类型暂不支持预览');
    return;
  }

  previewLoading.value = true;
  previewDialogVisible.value = true;
  previewTitle.value = `预览: ${file.name}`;
  previewContent.value = '';

  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

  try {
    const blobData = await down(file.id);
    if (!blobData || blobData.size === 0) {
      throw new Error('文件内容为空');
    }

    if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'].includes(ext)) {
      previewType.value = 'image';
      previewContent.value = window.URL.createObjectURL(blobData);
    } else if (['.txt', '.json', '.xml', '.log', '.md', '.py', '.js', '.java', '.c', '.cpp', '.h'].includes(ext)) {
      previewType.value = 'text';
      const text = await blobData.text();
      previewContent.value = text;
    } else {
      previewType.value = 'unknown';
    }

  } catch (error) {
    console.error('预览失败:', error);
    proxy.$message.error('预览加载失败');
    previewDialogVisible.value = false;
  } finally {
    previewLoading.value = false;
  }
}

function isPreviewable(file) {
  const previewableTypes = [
    // 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    // 文本
    '.txt', '.json', '.xml', '.log', '.md', '.py', '.js', '.java', '.c', '.cpp', '.h'
  ];
  if (!file || !file.name) return false;
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  return previewableTypes.includes(ext);
}

function parseTime(time, pattern) {
  if (!time) return '';

  if (arguments.length === 0 || !time) {
    return null;
  }
  const format = pattern || '{y}-{m}-{d} {h}:{i}:{s}';
  let date;
  if (typeof time === 'object') {
    date = time;
  } else {
    if ((typeof time === 'string') && (/^[0-9]+$/.test(time))) {
      time = parseInt(time);
    } else if (typeof time === 'string') {
      time = time.replace(new RegExp(/-/gm), '/');
    }
    if ((typeof time === 'number') && (time.toString().length === 10)) {
      time = time * 1000;
    }
    date = new Date(time);
  }
  const formatObj = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay()
  };
  const time_str = format.replace(/{(y|m|d|h|i|s|a)+}/g, (result, key) => {
    let value = formatObj[key];
    if (key === 'a') { return ['日', '一', '二', '三', '四', '五', '六'][value]; }
    if (result.length > 0 && value < 10) {
      value = '0' + value;
    }
    return value || 0;
  });
  return time_str;
}

// 初始化加载任务列表
getList();
</script>


<style scoped lang="scss">
.agri-business-page {
  --agri-primary: #3f9b62;
  --agri-primary-dark: #287b49;
  --agri-primary-light: #67b981;
  --agri-accent: #2c9c8d;
  --agri-bg: #f3f8f3;
  --agri-bg-soft: #edf6ef;
  --agri-card: rgba(255, 255, 255, 0.96);
  --agri-line: rgba(68, 139, 84, 0.16);
  --agri-line-strong: rgba(68, 139, 84, 0.26);
  --agri-text: #253d2d;
  --agri-text-soft: #5f7365;
  --agri-muted: #88978c;
  --agri-warning: #d89a32;
  --agri-danger: #d45f5f;

  position: relative;
  min-height: calc(100vh - 84px);
  padding: 18px 20px 26px;
  overflow: hidden;
  color: var(--agri-text);
  background:
    radial-gradient(circle at 4% 4%, rgba(91, 178, 116, 0.14), transparent 24%),
    radial-gradient(circle at 95% 8%, rgba(58, 163, 145, 0.10), transparent 22%),
    linear-gradient(180deg, #f7fbf7 0%, #eef6ef 100%);
}

.agri-business-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: "";
  opacity: 0.42;
  background-image:
    linear-gradient(rgba(64, 142, 83, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 142, 83, 0.025) 1px, transparent 1px);
  background-size: 34px 34px;
}

.agri-business-page > * {
  position: relative;
  z-index: 1;
}

/* 顶部标题 */
.analysis-page-header {
  margin-bottom: 16px;
}

/* 搜索筛选区 */
.analysis-filter-panel {
  position: relative;
  display: flex;
  padding: 20px 20px 4px;
  margin-bottom: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
  overflow: hidden;
  border: 1px solid var(--agri-line);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(241, 248, 242, 0.96));
  box-shadow:
    0 12px 30px rgba(53, 98, 63, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.80);
}

.analysis-filter-panel::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 170px;
  height: 4px;
  content: "";
  background: linear-gradient(90deg, var(--agri-primary), var(--agri-accent), transparent);
}

.analysis-filter-panel::after {
  position: absolute;
  top: -52px;
  right: -34px;
  width: 150px;
  height: 150px;
  border: 1px solid rgba(63, 155, 98, 0.08);
  border-radius: 50%;
  content: "";
}

.analysis-filter-panel :deep(.el-form-item) {
  margin-right: 18px;
  margin-bottom: 16px;
}

.analysis-filter-panel :deep(.el-form-item__label) {
  color: #3d5945;
  font-size: 13px;
  font-weight: 650;
}

.analysis-filter-panel :deep(.el-input__wrapper),
.analysis-filter-panel :deep(.el-select__wrapper) {
  min-height: 38px;
  border: 1px solid rgba(68, 139, 84, 0.14);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.90);
  box-shadow: none;
  transition: all 0.2s ease;
}

.analysis-filter-panel :deep(.el-input__wrapper:hover),
.analysis-filter-panel :deep(.el-select__wrapper:hover) {
  border-color: rgba(63, 155, 98, 0.36);
}

.analysis-filter-panel :deep(.el-input__wrapper.is-focus),
.analysis-filter-panel :deep(.el-select__wrapper.is-focused) {
  border-color: var(--agri-primary);
  box-shadow: 0 0 0 3px rgba(63, 155, 98, 0.09);
}

.analysis-filter-panel :deep(.el-input__inner),
.analysis-filter-panel :deep(.el-select__selected-item),
.analysis-filter-panel :deep(.el-select__placeholder) {
  color: #425649;
  font-size: 12px;
}

/* 操作工具栏 */
.analysis-toolbar {
  position: relative;
  min-height: 58px;
  padding: 11px 14px;
  margin-bottom: 12px !important;
  align-items: center;
  border: 1px solid var(--agri-line);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 8px 22px rgba(53, 98, 63, 0.06);
  backdrop-filter: blur(8px);
}

.analysis-toolbar::before {
  display: inline-flex;
  min-width: 88px;
  height: 34px;
  margin-right: 12px;
  padding: 0 12px;
  align-items: center;
  justify-content: center;
  color: #41604a;
  border: 1px solid rgba(68, 139, 84, 0.13);
  border-radius: 9px;
  background: #f2f8f3;
  content: "任务操作";
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.analysis-toolbar :deep(.el-button) {
  min-height: 36px;
  padding: 8px 15px;
  border-radius: 9px;
  font-weight: 650;
}

.analysis-toolbar :deep(.el-button--primary.is-plain) {
  color: #347f4f;
  border-color: rgba(63, 155, 98, 0.28);
  background: rgba(63, 155, 98, 0.07);
}

.analysis-toolbar :deep(.el-button--success.is-plain) {
  color: #2e8978;
  border-color: rgba(44, 156, 141, 0.26);
  background: rgba(44, 156, 141, 0.07);
}

.analysis-toolbar :deep(.el-button--danger.is-plain) {
  color: #c15151;
  border-color: rgba(212, 95, 95, 0.22);
  background: rgba(212, 95, 95, 0.06);
}

/* 主任务表格 */
.analysis-task-table {
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--agri-line);
  border-radius: 18px;
  background: var(--agri-card);
  box-shadow:
    0 15px 38px rgba(53, 98, 63, 0.09),
    inset 0 1px 0 rgba(255, 255, 255, 0.76);
  --el-table-border-color: rgba(68, 139, 84, 0.09);
  --el-table-header-bg-color: #edf6ef;
  --el-table-row-hover-bg-color: #f0f8f2;
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.95);
  --el-fill-color-lighter: #f8fbf8;
}

.analysis-task-table::before,
.analysis-task-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.analysis-task-table :deep(.el-table__header-wrapper th.el-table__cell) {
  height: 54px;
  padding: 0;
  color: #36583f;
  border-bottom: 1px solid rgba(68, 139, 84, 0.14);
  background:
    linear-gradient(180deg, #f3f9f4 0%, #eaf4ec 100%);
  font-size: 12px;
  font-weight: 750;
}

.analysis-task-table :deep(.el-table__header-wrapper .cell) {
  padding: 0 10px;
  line-height: 54px;
  white-space: nowrap;
}

.analysis-task-table :deep(.el-table__body-wrapper td.el-table__cell) {
  height: 62px;
  padding: 0;
  color: #4e6153;
  border-bottom: 1px solid rgba(68, 139, 84, 0.075);
  background: transparent;
  font-size: 12px;
}

.analysis-task-table :deep(.el-table__body-wrapper .cell) {
  padding: 0 10px;
  line-height: 1.45;
  word-break: break-word;
}

.analysis-task-table :deep(.el-table__row--striped td.el-table__cell) {
  background: rgba(247, 251, 248, 0.88);
}

.analysis-task-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #edf7ef !important;
}

.analysis-task-table :deep(.el-checkbox__inner) {
  border-color: rgba(63, 155, 98, 0.35);
  border-radius: 5px;
}

.analysis-task-table :deep(.el-checkbox__input.is-checked .el-checkbox__inner),
.analysis-task-table :deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  border-color: var(--agri-primary);
  background: var(--agri-primary);
}

.analysis-task-table :deep(.el-tag) {
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}

.analysis-task-table :deep(.el-tag--success) {
  color: #347d4c;
  border-color: rgba(63, 155, 98, 0.20);
  background: rgba(63, 155, 98, 0.08);
}

.analysis-task-table :deep(.el-tag--warning) {
  color: #a76f16;
  border-color: rgba(216, 154, 50, 0.22);
  background: rgba(216, 154, 50, 0.09);
}

.analysis-task-table :deep(.el-tag--danger) {
  color: #b74c4c;
  border-color: rgba(212, 95, 95, 0.20);
  background: rgba(212, 95, 95, 0.08);
}

.analysis-task-table :deep(.el-tag--primary) {
  color: #317769;
  border-color: rgba(44, 156, 141, 0.22);
  background: rgba(44, 156, 141, 0.08);
}

.analysis-task-table :deep(.el-button.is-link) {
  height: 27px;
  padding: 0 6px;
  color: #3f8f5a;
  border-radius: 6px;
  font-size: 11px;
}

.analysis-task-table :deep(.el-button.is-link:hover) {
  color: #246f43;
  background: rgba(63, 155, 98, 0.08);
}

.analysis-task-table :deep(.el-button.is-link .el-icon) {
  margin-right: 3px;
}

.no-result {
  color: var(--agri-muted);
  font-size: 11px;
}

/* 主分页 */
.analysis-main-pagination {
  padding: 14px 16px 4px;
}

.analysis-main-pagination :deep(.pagination-container) {
  margin: 0;
  padding: 12px 16px;
  border: 1px solid var(--agri-line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.87);
  box-shadow: 0 8px 22px rgba(53, 98, 63, 0.06);
}

/* 文件选择与参数区域 */
.file-selection-container,
.param-container {
  width: 100%;
  padding: 16px;
  border: 1px solid var(--agri-line);
  border-radius: 14px;
  background:
    linear-gradient(145deg, #fbfefb, #f1f8f2);
}

.file-selection-header,
.param-header {
  display: flex;
  min-height: 42px;
  padding-bottom: 11px;
  margin-bottom: 12px;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(68, 139, 84, 0.12);
}

.file-selection-title,
.param-title {
  color: #31513a;
  font-size: 14px;
  font-weight: 750;
}

.selected-files-list {
  max-height: 270px;
  padding-right: 4px;
  margin-bottom: 12px;
  overflow-y: auto;
}

.selected-file-item {
  display: flex;
  min-height: 48px;
  padding: 9px 11px;
  margin-bottom: 8px;
  align-items: center;
  justify-content: space-between;
  border: 1px solid rgba(68, 139, 84, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.86);
  transition: all 0.2s ease;
}

.selected-file-item:hover {
  border-color: rgba(63, 155, 98, 0.28);
  box-shadow: 0 7px 18px rgba(53, 98, 63, 0.07);
  transform: translateY(-1px);
}

.file-info {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
}

.file-info .el-icon {
  color: var(--agri-primary);
  font-size: 18px;
}

.file-name {
  overflow: hidden;
  color: #3f5846;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.file-size,
.more-files,
.current-folder,
.no-params-tip,
.param-intro {
  color: var(--agri-muted);
  font-size: 11px;
}

.selected-count {
  padding: 9px 12px;
  color: #357b4c;
  border: 1px solid rgba(63, 155, 98, 0.14);
  border-radius: 9px;
  background: rgba(63, 155, 98, 0.07);
  text-align: center;
  font-size: 12px;
  font-weight: 650;
}

.no-files-tip {
  padding: 22px;
  color: var(--agri-muted);
  text-align: center;
}

.algorithm-params-info {
  padding: 14px 15px;
  margin-bottom: 13px;
  border: 1px solid rgba(44, 156, 141, 0.15);
  border-radius: 11px;
  background: rgba(44, 156, 141, 0.045);
}

.algorithm-params-info h4 {
  margin: 0 0 10px;
  color: #317769;
  font-size: 13px;
}

.param-info-item {
  padding: 5px 0;
  color: #576b5d;
  font-size: 12px;
}

.param-name {
  margin-right: 7px;
  color: #35533e;
  font-weight: 700;
}

.param-default {
  color: #b37b22;
  font-size: 11px;
}

.param-item {
  padding: 15px;
  margin-bottom: 12px;
  border: 1px solid rgba(68, 139, 84, 0.13);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.90);
}

.param-item-header {
  display: flex;
  padding-bottom: 10px;
  margin-bottom: 12px;
  align-items: center;
  justify-content: space-between;
  color: #31513a;
  border-bottom: 1px solid rgba(68, 139, 84, 0.10);
  font-size: 13px;
  font-weight: 750;
}

.file-param-input {
  display: flex;
  width: 100%;
  align-items: center;
}

.file-param-info {
  margin-top: 7px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 22px;
}

/* 文件树和列表 */
.file-selection-dialog {
  min-height: 560px;
}

.folder-tree-panel,
.file-list-panel {
  display: flex;
  height: 510px;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid var(--agri-line);
  border-radius: 14px;
  background: #fbfefb;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.76);
}

.panel-header {
  display: flex;
  min-height: 58px;
  padding: 12px 15px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid rgba(68, 139, 84, 0.12);
  background:
    linear-gradient(180deg, #f3f9f4, #edf6ef);
}

.panel-header h4 {
  margin: 0;
  color: #31513a;
  font-size: 14px;
  font-weight: 750;
}

.tree-container {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}

.custom-tree-node {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  color: #4f6556;
  font-size: 12px;
}

.custom-tree-node .el-icon {
  color: var(--agri-primary);
}

:deep(.el-tree) {
  color: #4f6556;
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 38px;
  border-radius: 8px;
}

:deep(.el-tree-node__content:hover),
:deep(.el-tree-node:focus > .el-tree-node__content) {
  background: rgba(63, 155, 98, 0.08);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  color: #2e7548;
  background: rgba(63, 155, 98, 0.12);
}

:deep(.el-tree-node__expand-icon) {
  color: #5a9e6e;
}

.file-list-panel :deep(.el-table) {
  margin: 0;
}

.pagination {
  display: flex;
  margin-top: 12px;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  padding-top: 15px;
  margin-top: 16px;
  align-items: flex-start;
  justify-content: space-between;
  border-top: 1px solid rgba(68, 139, 84, 0.12);
}

.selected-info {
  flex: 1;
}

.selected-preview {
  max-width: 520px;
  margin-top: 8px;
}

/* 预览 */
.preview-container {
  display: flex;
  min-height: 220px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid var(--agri-line);
  border-radius: 12px;
  background: #f6faf7;
}

:deep(.el-empty__description) {
  color: var(--agri-muted);
}

/* 页面内通用 Element Plus 控件 */
.agri-business-page :deep(.el-button) {
  border-radius: 9px;
}

.agri-business-page :deep(.el-button--primary) {
  border-color: #3f9b62;
  background: linear-gradient(180deg, #5eb378, #3f9b62);
  box-shadow: 0 5px 14px rgba(63, 155, 98, 0.16);
}

.agri-business-page :deep(.el-button--primary:hover) {
  border-color: #4fa96e;
  background: linear-gradient(180deg, #6abc83, #4ca76a);
}

.agri-business-page :deep(.el-button--primary.is-plain) {
  color: #347f4f;
  border-color: rgba(63, 155, 98, 0.28);
  background: rgba(63, 155, 98, 0.07);
  box-shadow: none;
}

.agri-business-page :deep(.el-input__wrapper),
.agri-business-page :deep(.el-select__wrapper),
.agri-business-page :deep(.el-textarea__inner) {
  border: 1px solid rgba(68, 139, 84, 0.14);
  border-radius: 9px;
  background: #ffffff;
  box-shadow: none;
}

.agri-business-page :deep(.el-input__wrapper.is-focus),
.agri-business-page :deep(.el-select__wrapper.is-focused),
.agri-business-page :deep(.el-textarea__inner:focus) {
  border-color: var(--agri-primary);
  box-shadow: 0 0 0 3px rgba(63, 155, 98, 0.08);
}

/* 响应式 */
@media (max-width: 1500px) {
  .analysis-filter-panel :deep(.el-form-item) {
    margin-right: 12px;
  }

  .analysis-filter-panel :deep(.el-input),
  .analysis-filter-panel :deep(.el-select) {
    width: 210px !important;
  }

  .analysis-task-table :deep(.el-table__header-wrapper .cell),
  .analysis-task-table :deep(.el-table__body-wrapper .cell) {
    padding: 0 7px;
  }
}

@media (max-width: 1100px) {
  .agri-business-page {
    padding: 14px;
    overflow-x: auto;
  }

  .analysis-filter-panel {
    min-width: 980px;
  }

  .analysis-toolbar,
  .analysis-task-table,
  .analysis-main-pagination {
    min-width: 1180px;
  }
}
</style>

<style lang="scss">
/* 弹窗挂载到 body，使用全局样式 */
.analysis-task-dialog,
.analysis-file-dialog,
.analysis-result-dialog,
.analysis-preview-dialog {
  overflow: hidden;
  border: 1px solid rgba(68, 139, 84, 0.18);
  border-radius: 18px;
  background: #fbfefb;
  box-shadow: 0 24px 70px rgba(35, 77, 45, 0.22);
}

.analysis-task-dialog .el-dialog__header,
.analysis-file-dialog .el-dialog__header,
.analysis-result-dialog .el-dialog__header,
.analysis-preview-dialog .el-dialog__header {
  padding: 18px 22px;
  margin: 0;
  border-bottom: 1px solid rgba(68, 139, 84, 0.13);
  background:
    linear-gradient(90deg, #edf7ef 0%, #f8fcf8 72%);
}

.analysis-task-dialog .el-dialog__title,
.analysis-file-dialog .el-dialog__title,
.analysis-result-dialog .el-dialog__title,
.analysis-preview-dialog .el-dialog__title {
  color: #294d33;
  font-size: 16px;
  font-weight: 760;
}

.analysis-task-dialog .el-dialog__header::before,
.analysis-file-dialog .el-dialog__header::before,
.analysis-result-dialog .el-dialog__header::before,
.analysis-preview-dialog .el-dialog__header::before {
  display: inline-block;
  width: 4px;
  height: 17px;
  margin-right: 9px;
  vertical-align: -3px;
  border-radius: 4px;
  background: linear-gradient(180deg, #43a767, #2c9c8d);
  content: "";
}

.analysis-task-dialog .el-dialog__body,
.analysis-file-dialog .el-dialog__body,
.analysis-result-dialog .el-dialog__body,
.analysis-preview-dialog .el-dialog__body {
  padding: 20px 22px 22px;
  color: #4d6253;
  background:
    radial-gradient(circle at 94% 2%, rgba(63, 155, 98, 0.07), transparent 22%),
    #fbfefb;
}

.analysis-task-dialog .el-dialog__headerbtn,
.analysis-file-dialog .el-dialog__headerbtn,
.analysis-result-dialog .el-dialog__headerbtn,
.analysis-preview-dialog .el-dialog__headerbtn {
  top: 15px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.analysis-task-dialog .el-dialog__headerbtn:hover,
.analysis-file-dialog .el-dialog__headerbtn:hover,
.analysis-result-dialog .el-dialog__headerbtn:hover,
.analysis-preview-dialog .el-dialog__headerbtn:hover {
  background: rgba(63, 155, 98, 0.08);
}

.analysis-task-dialog .el-steps {
  padding: 16px 12px;
  border: 1px solid rgba(68, 139, 84, 0.12);
  border-radius: 13px;
  background: #f4f9f5;
}

.analysis-task-dialog .el-step__icon {
  width: 30px;
  height: 30px;
  border-color: rgba(63, 155, 98, 0.30);
  background: #ffffff;
}

.analysis-task-dialog .el-step__head.is-process,
.analysis-task-dialog .el-step__title.is-process,
.analysis-task-dialog .el-step__head.is-finish,
.analysis-task-dialog .el-step__title.is-finish {
  color: #3f9b62;
  border-color: #3f9b62;
}

.analysis-task-dialog .el-step__line {
  background: rgba(68, 139, 84, 0.16);
}

.analysis-task-dialog .el-form-item__label,
.analysis-file-dialog .el-form-item__label,
.analysis-result-dialog .el-form-item__label {
  color: #3f5947;
  font-weight: 650;
}

.analysis-task-dialog .el-input__wrapper,
.analysis-task-dialog .el-select__wrapper,
.analysis-task-dialog .el-textarea__inner,
.analysis-file-dialog .el-input__wrapper,
.analysis-file-dialog .el-select__wrapper,
.analysis-result-dialog .el-input__wrapper {
  border: 1px solid rgba(68, 139, 84, 0.15);
  border-radius: 9px;
  box-shadow: none;
}

.analysis-task-dialog .el-input__wrapper.is-focus,
.analysis-task-dialog .el-select__wrapper.is-focused,
.analysis-task-dialog .el-textarea__inner:focus,
.analysis-file-dialog .el-input__wrapper.is-focus,
.analysis-result-dialog .el-input__wrapper.is-focus {
  border-color: #3f9b62;
  box-shadow: 0 0 0 3px rgba(63, 155, 98, 0.08);
}

.analysis-file-dialog .el-table,
.analysis-result-dialog .el-table {
  overflow: hidden;
  border: 1px solid rgba(68, 139, 84, 0.12);
  border-radius: 11px;
  --el-table-header-bg-color: #edf6ef;
  --el-table-row-hover-bg-color: #f0f8f2;
}

.analysis-file-dialog .el-table th.el-table__cell,
.analysis-result-dialog .el-table th.el-table__cell {
  color: #36583f;
  background: #edf6ef;
  font-weight: 700;
}

.analysis-file-dialog .el-pagination,
.analysis-result-dialog .el-pagination {
  --el-pagination-hover-color: #3f9b62;
}

.analysis-preview-dialog pre {
  width: 100%;
  max-height: 520px;
  padding: 16px !important;
  margin: 0;
  overflow-y: auto;
  color: #dff3e4 !important;
  border-radius: 10px;
  background: #10271a !important;
  font-family: Consolas, "Courier New", monospace;
  line-height: 1.65;
}
</style>

